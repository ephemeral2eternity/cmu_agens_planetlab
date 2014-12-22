/*

  MultiQuery

  an EXPERIMENTAL distributed command execution tool for PlanetLab

  Given a list of nodes and a command, it executes that command
  on all of the nodes and returns results as they arrive. Can also
  be compiled as multicopy and used to perform multiple scp

  example: ./multiquery ls -l
  ./multicopy localfilename @:

  the "@:" in multicopy gets expanded to the remote machine name

  How to set up: 
  The configuration is controlled via environment variables

  mandatory:
  MQ_SLICE - your planetlab slice login name, e.g., princeton9
             this can be left blank if your ssh config already
             handles the login name
  MQ_NODES - a file that contains a list of planetlab nodes, one per line

  optional:
  MQ_TIMEOUT - seconds to wait before killing the remaining queries, 
               default 30 seconds
  MQ_DELAY - seconds to wait between starting ssh commands, default 0
  MQ_ORDER - if set to 1, forces in-order display of results
  MQ_MAXLOAD - specifies the maximum number of open connections

  comments, feedback, bug reports to Vivek Pai, vivek@cs.princeton.edu
  Note: this is still experimental, use with caution

  NOTES: currently, all commands must be specified on the command line.
  I intend to allow commands via stdin at some point in the future

  Added probing support before actually opening ssh/sftp port.
  Any bug/commment should be directo to Aki Nakao, nakao@cs.princeton.edu
  
 */

#include <sys/wait.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/utsname.h>
#include <netdb.h>
#include <time.h>
#include <fcntl.h>
#include <errno.h>

#include "applib.h"

#ifdef __sparc
typedef uint32_t u_int32_t;
typedef uint16_t u_int16_t;
#define inet_aton(name, addr) inet_pton(AF_INET, name, addr)
#endif

#define PROBE_PORT 22
#define PROBE_TIMEOUT 10       /* seconds */

static char *whichSSH = "/usr/local/bin/ssh";

typedef struct NodeInfo {
  char *ni_name;
  pid_t ni_pid;
  char *ni_buffer;		/* returned data, only if in-order */
  int ni_bufferUsed;		/* amount used, only if in-order */
  struct timeval ni_killTime;	/* when should it be killed */
  int ni_fd;			/* which socket connects to it */
} NodeInfo;

static NodeInfo *nodeList;
static int nodeListSize;
static int waitingToFinish = 0; /* which item should finish */

static char *envSliceName;
static char *envNodeListFile;
static char *envTimeout = "30";
static char *envDelayStr = "0.5";
static float envDelay;
static int maxLoad = 5;		/* max # outstanding requests */

static int isMaster = 1;	/* master process or child? */
static int inOrder = 0;		/* do we present results in order? */
static int needsPrinting = 0;	/* what to print next */

static fd_set readSet;
static int maxReadSetFD;

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif

HANDLE hdebugLog = NULL;

/*-----------------------------------------------------------------*/
static void *
GeneralRealloc(void *buf, int used, int *alloc, int minAlloc, int itemSize)
{
  /* basically used to make sure that there's enough space in the
     buffer for whatever needs to be added, and if not, grows it
     in a reasonably sane way */
  int newAlloc;
  char *bufChar;

  if (used + minAlloc < *alloc)
    return(buf);
  if (minAlloc < 1)
    minAlloc = 1;

  newAlloc = used * 2;
  if (newAlloc < used + minAlloc)
    newAlloc = used + minAlloc;
  if ((buf = realloc(buf, newAlloc * itemSize)) == NULL) {
    fprintf(stderr, "error: failed realloc\n");
    exit(-1);
  }

  bufChar = buf;
  memset(&bufChar[used * itemSize], 0, (newAlloc - used) * itemSize);
  *alloc = newAlloc;
  return(buf);
}
/*-----------------------------------------------------------------*/
static void
GetNodeList(char *filename)
{
  FILE *list;
  int nodeListAlloc = 0;
  char *temp;

  if ((list = fopen(filename, "r")) == NULL) {
    fprintf(stderr, "error: couldn't open %s\n", filename);
    exit(-1);
  }

  while ((temp = GetLowerNextLine(list)) != NULL) {
    /* reallocate list if needed */
    nodeList = GeneralRealloc(nodeList, nodeListSize, &nodeListAlloc, 
			      4, sizeof(NodeInfo));
    nodeList[nodeListSize].ni_name = temp;
    nodeListSize++;
  }
  fclose(list);
}
/*-----------------------------------------------------------------*/
static char *
BuildCommand(char *nodeName, int argc, char *argv[])
{
  int i;
  char command[65536];		/* please don't overflow :-) */

  if (strstr(argv[0], "multicopy")) {
    int len = 0;

    sprintf(command, "scp -r -p");
    len = strlen(command);

    for (i = 1; i < argc; i++) {
      char *arg = argv[i];
      int argLen = strlen(arg);
      int j;

      command[len] = ' ';
      len++;
      for (j = 0; j < argLen; j++) {
	if (arg[j] != '@') {
	  /* if not an @ sign, just copy it */
	  command[len] = arg[j];
	  len++;
	  continue;
	}
	if (j == 0 && arg[1] == ':') {
	  /* if we see @: at the beginning of an argument, substitute
	     with user and machine name */
	  sprintf(&command[len], "%s%s", envSliceName, nodeName);
	}
	else {
	  /* if it's in the middle, or if it's not trying to log in,
	     just put in the machine name */
	  sprintf(&command[len], "%s", nodeName);
	}
	len += strlen(&command[len]);
      }
    }
    command[len] = 0; /* make it null-terminated */
    strcat(command, " && echo done");
  }
  else {
    sprintf(command, "%s -n -T %s%s '", whichSSH, envSliceName, nodeName);

    for (i = 1; i < argc; i++) {
      sprintf(&command[strlen(command)], "%s%s", argv[i],
	      (i == argc-1) ? "" : " ");
    }
    
    strcat(command, "'");
  }

  return(strdup(command));
}
/*-----------------------------------------------------------------*/
static int
NameToIP(char *hostname, struct in_addr *inaddr)
{
  struct hostent *hp;
  if (!inet_aton(hostname, inaddr)) {
    hp = gethostbyname(hostname);
    if (!hp) 
      return -1;
    memcpy(inaddr, hp->h_addr, sizeof(struct in_addr));
  }
  return 0;
}
/*-----------------------------------------------------------------*/
static int
TestPortOpenness(char *host, u_int16_t port, int waitSecs)
{
  u_int32_t ip = 0;
  int ret = FAILURE;
  struct sockaddr_in dest;
  int sock = -1;  
  fd_set writeFds;
  struct timeval timeout;
  
  NameToIP(host, (struct in_addr *) &ip);

  /* set addr structure */
  memset(&dest, 0, sizeof(dest));
  dest.sin_family = AF_INET;
  dest.sin_port = htons(port);
  dest.sin_addr.s_addr = ip;

  /* create socket */
  if ((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0) {
    perror("socket");
    return(FAILURE);
  }
  
  /* make socket non-blocking */
  if (fcntl(sock, F_SETFL, O_NONBLOCK) < 0)
    perror("fcntl");
  
  /* we expect that the connection is in progress and we have
     a timeout period - if neither is true, fail */
  if (connect(sock, (struct sockaddr *) &dest, sizeof(dest)) != -1 || 
      errno != EINPROGRESS) {
    perror("connect");
    goto done;
  }
  
  /* select on the fd and wait until the timer expires or the fd
     becomes ready */
  FD_ZERO(&writeFds);
  FD_SET(sock, &writeFds);
  timeout.tv_sec = waitSecs;
  timeout.tv_usec = 0;
  
  if (select(sock+1, NULL, &writeFds, NULL, &timeout) > 0 && 
      FD_ISSET(sock, &writeFds)) {
    /* we're happy - this is what we expected */
    ret = SUCCESS;
  }

 done:
  if (sock >= 0)
    close(sock);
  return(ret);
}
/*-----------------------------------------------------------------*/
static void
QueryNode(char *command, char *nodeName)
{
  FILE *resp;
  char *readBuf = NULL;
  int readBufAlloc = 0;
  int readBufUsed = 0;
  int res;

  /* check if node accepts tcp port PROBE_PORT*/
  if (TestPortOpenness(nodeName, PROBE_PORT, PROBE_TIMEOUT) != SUCCESS) {
    fprintf(stdout, "%s: timed out probe\n", nodeName);
    fflush(stdout);
    return;
  }

  if ((resp = popen(command, "r")) == NULL) {
    fprintf(stderr, "error: couldn't popen, node %s\n", nodeName);
    exit(-1);
  }

  while (1) {
    readBuf = GeneralRealloc(readBuf, readBufUsed, &readBufAlloc, 
			     512, sizeof(char));
    res = read(fileno(resp), &readBuf[readBufUsed], 
	       readBufAlloc - readBufUsed);
    if (res >= 1)
      readBufUsed += res;
    else {
      if (res == -1 && errno == EINTR)
	continue;
      if (readBuf != NULL) {
	fprintf(stdout, "%s: %d bytes\n", nodeName, readBufUsed);
	fflush(stdout);
	write(STDOUT_FILENO, readBuf, readBufUsed);
	free(readBuf);
      }
      pclose(resp);
      return;
    }
  }
}
/*-----------------------------------------------------------------*/
static int
LaunchNewProcess(char *command, int whichNode)
{
  int socks[2];
  pid_t pid;

  if (command == NULL) {
    fprintf(stderr, "error: couldn't build command, node %s\n",
	    nodeList[whichNode].ni_name);
    exit(-1);
  }
  
  if (pipe(socks) < 0) {
    fprintf(stderr, "error: pipe failed, node %s\n", 
	    nodeList[whichNode].ni_name);
    exit(-1);
  }
  
  pid = fork();
  if (pid == 0) {
    int j;
    /* child */
    isMaster = 0;
    close(socks[0]);		/* close read end */
    
    /* set stdout to be this pipe end */
    if (dup2(socks[1], STDOUT_FILENO) < 0) {
      fprintf(stderr, "error: dup2 failed, node %s\n", 
	      nodeList[whichNode].ni_name);
      exit(-1);
    }
    
    /* close all unneeded descriptors */
    for (j = STDERR_FILENO+1; j < FD_SETSIZE; j++)
      close(j);
    
    /* launch the query */
    QueryNode(command, nodeList[whichNode].ni_name);
    exit(0);
  }

  /* parent */
  nodeList[whichNode].ni_pid = pid;
  close(socks[1]);		/* close write end */

  FD_SET(socks[0], &readSet);
  if (socks[0] > maxReadSetFD)
    maxReadSetFD = socks[0];
  return(socks[0]);		/* return read end */
}
/*-----------------------------------------------------------------*/
static void
SafeWrite(char *buf, int len)
{
  while (len) {
    int res = write(STDOUT_FILENO, buf, len);
    if (res < 0) {
      if (errno == EINTR)
	continue;
      fprintf(stderr, "error in write\n");
      exit(-1);
    }
    buf += res;
    len -= res;
  }
}
/*-----------------------------------------------------------------*/
static void
ReadAndClose(int fd, int whichNode)
{
  char buf[1024];
  int res;
  int alloc = 0;
  NodeInfo *node = &nodeList[whichNode];
  int saveThis = 0;

  /* buffer it only if inOrder and this isn't next */
  if (inOrder) {
    if (needsPrinting == whichNode)
      needsPrinting++;
    else
      saveThis = 1;
  }

  while (1) {
    res = read(fd, buf, sizeof(buf));
    if (res > 0) {
      if (saveThis) {
	node->ni_buffer = GeneralRealloc(node->ni_buffer, node->ni_bufferUsed, 
					 &alloc, 1024, sizeof(char));
	memcpy(&node->ni_buffer[node->ni_bufferUsed], buf, res);
	node->ni_bufferUsed += res;
      }
      else
	SafeWrite(buf, res);
    }
    else {
      if (res == -1 && errno == EINTR)
	continue;
      if (!saveThis) {
	fprintf(stdout, "\n");
	fflush(stdout);
      }
      if (res < 0)
	fprintf(stderr, "error: reading from pipe, node %s\n",
		node->ni_name);
      close(fd);
      return;
    }
  }
}
/*-----------------------------------------------------------------*/
static void
ChildHandler(int sig)
{
  pid_t pid;

  do {
    pid = wait3(NULL, WNOHANG, NULL);
  } while (pid && pid != -1);

  signal(SIGCHLD, ChildHandler);  
}
/*-----------------------------------------------------------------*/
static void
TerminateHandler(int sig)
{
  /* kill off any remaining processes */
  int i;
  int killed = 0;

  if (isMaster) {
    for (i = 0; i < nodeListSize; i++) {
      if (nodeList[i].ni_pid) {
	kill(nodeList[i].ni_pid, SIGKILL);
	killed++;
      }
    }
  }

  exit(-1);
}
/*-----------------------------------------------------------------*/
static void
PrintInOrderBufs(void)
{
  if (!inOrder)
    return;
  while (needsPrinting < nodeListSize &&
	 nodeList[needsPrinting].ni_buffer != NULL) {
    SafeWrite(nodeList[needsPrinting].ni_buffer, 
	      nodeList[needsPrinting].ni_bufferUsed);
    fprintf(stdout, "\n");
    fflush(stdout);
    needsPrinting++;
  }
}
/*-----------------------------------------------------------------*/
static struct timeval now;
static struct timeval nextLaunchTime;
static int numLaunched;
static int numFinished;
/*-----------------------------------------------------------------*/
static int
BuildAndLaunch(int whichNode, int argc, char *argv[])
{
  char *command = BuildCommand(nodeList[whichNode].ni_name, argc, argv);
  int fd;
  
  fd = LaunchNewProcess(command, whichNode);
  
  free(command);

  /* calculate next launch time */
  nextLaunchTime.tv_sec = now.tv_sec;
  nextLaunchTime.tv_usec = now.tv_usec + 1e6 * envDelay;
  if (nextLaunchTime.tv_usec >= 1e6) {
    int secs = nextLaunchTime.tv_usec / 1e6;
    nextLaunchTime.tv_sec += secs;
    nextLaunchTime.tv_usec -= secs * 1e6;
  }

  nodeList[numLaunched].ni_killTime = now;
  nodeList[numLaunched].ni_killTime.tv_sec += atoi(envTimeout);
  
  return(fd);
}
/*-----------------------------------------------------------------*/
static int
NeedsLaunch(void)
{
  if (numLaunched >= nodeListSize ||
      numLaunched - numFinished >= maxLoad)
    return(FALSE);

  if (now.tv_sec < nextLaunchTime.tv_sec ||
      (now.tv_sec == nextLaunchTime.tv_sec &&
       now.tv_usec < nextLaunchTime.tv_usec))
    return(FALSE);
  return(TRUE);
}
/*-----------------------------------------------------------------*/
static void
CalcTimeout(struct timeval *timeout)
{
  if (numLaunched < nodeListSize &&
      numLaunched - numFinished  < maxLoad) {
    timeout->tv_sec = floor(envDelay);
    timeout->tv_usec = 1e6 * (envDelay - timeout->tv_sec);
  }
  else {
    timeout->tv_sec = 1;
    timeout->tv_usec = 0;
  }
}
/*-----------------------------------------------------------------*/
int
main(int argc, char *argv[])
{
  int i;
  int nodeMap[FD_SETSIZE];
  int bad = 0;

  if (access(whichSSH, X_OK) != 0) {
    whichSSH = "/usr/bin/ssh";
    if (access(whichSSH, X_OK) != 0) {
      whichSSH = "ssh";
      if (access(whichSSH, X_OK) != 0) {
	fprintf(stderr, "couldn't find ssh\n");
	exit(-1);
      }
    }
  }

  signal(SIGCHLD, ChildHandler);  
  signal(SIGINT, TerminateHandler);  

  FD_ZERO(&readSet);

  for (i = 0; i < FD_SETSIZE; i++)
    nodeMap[i] = -1;

  if ((envSliceName = getenv("MQ_SLICE")) == NULL) {
    fprintf(stderr, 
	    "warning: you may need to set MQ_SLICE to login, "
	    "e.g., setenv MQ_SLICE princeton9\n");
    envSliceName = "";
  }
  else {
    char buf[256];
    sprintf(buf, "%s@", envSliceName);
    envSliceName = strdup(buf);
  }

  if ((envNodeListFile = getenv("MQ_NODES")) == NULL) {
    bad = 1;
    fprintf(stderr, 
	    "error: set MQ_NODES to node list, "
	    "e.g., setenv MQ_NODES node_list\n");
  }

  if (getenv("MQ_TIMEOUT") != NULL)
    envTimeout = getenv("MQ_TIMEOUT");

  if (getenv("MQ_DELAY") != NULL) {
    envDelayStr = getenv("MQ_DELAY");
    envDelay = atof(envDelayStr);
  }

  if (getenv("MQ_ORDER") != NULL)
    inOrder = atoi(getenv("MQ_ORDER"));

  if (getenv("MQ_MAXLOAD") != NULL)
    maxLoad = atoi(getenv("MQ_MAXLOAD"));

  if (bad)
    exit(-1);

  GetNodeList(envNodeListFile);

  if (nodeListSize < 1) {
    fprintf(stderr, "error: couldn't find anything in %s\n", 
	    envNodeListFile);
    exit(-1);
  }

  if (argc < 2) {
    fprintf(stderr, "error: must give command on command line\n");
    exit(-1);
  }

  fprintf(stderr, "command is %s\n",
	  BuildCommand("machine", argc, argv));
	  
  while (numFinished < nodeListSize) {
    fd_set tempSet;
    struct timeval timeout;
    int ready;

    gettimeofday(&now, NULL);

    if (NeedsLaunch()) {
      /* launch a new one */
      int fd;
      
      fd = BuildAndLaunch(numLaunched, argc, argv);
      nodeMap[fd] = numLaunched;
      nodeList[numLaunched].ni_fd = fd;
      numLaunched++;
    }

    CalcTimeout(&timeout);

    tempSet = readSet;

    ready = select(maxReadSetFD+1, &tempSet, NULL, NULL, &timeout);
    if (ready <= 0) {
      if (ready < 0) {
	if (errno == EINTR)
	  continue;
	fprintf(stderr, "error: select returned error\n");
	exit(-1);
      }

      gettimeofday(&now, NULL);
      
      /* see if any connections should be timed out */
      while (waitingToFinish < numLaunched &&
	     nodeList[waitingToFinish].ni_killTime.tv_sec < now.tv_sec) {
	fprintf(stdout, "%s: timed out ssh\n\n", 
		nodeList[waitingToFinish].ni_name);
	fflush(stdout);
	kill(nodeList[waitingToFinish].ni_pid, SIGKILL);
	nodeList[waitingToFinish].ni_pid = 0;
	FD_CLR(nodeList[waitingToFinish].ni_fd, &readSet);
	needsPrinting = waitingToFinish+1;
	PrintInOrderBufs();
	waitingToFinish++;
	numFinished++;
	while (waitingToFinish < numLaunched &&
	       nodeList[waitingToFinish].ni_pid == 0)
	  waitingToFinish++;
      }
      
      if (numFinished < nodeListSize)
	continue;

      exit(-1);
    }

    for (i = 0; i < FD_SETSIZE; i++) {
      if (!FD_ISSET(i, &tempSet))
	continue;
      
      FD_CLR(i, &readSet);
      numFinished++;
      ReadAndClose(i, nodeMap[i]);
      nodeList[nodeMap[i]].ni_pid = 0;
      nodeMap[i] = -1;	/* done with entry */
      while (waitingToFinish < numLaunched &&
	     nodeList[waitingToFinish].ni_pid == 0)
	waitingToFinish++;
      PrintInOrderBufs();
    }
  }

  return(0);
}
/*-----------------------------------------------------------------*/
