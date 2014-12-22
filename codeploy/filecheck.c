/*
  checks various files on planetlab nodes to see what's out-of-date
  
*/

#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include "applib.h"
#include "parsequery.h"

#define MAX_FILES 1000
#define MAX_NODES 400

#define FILECHECKLIST "filechecklist.txt"

#ifdef __linux__
#define SORT "/bin/sort"
#else
#define SORT "/usr/bin/sort"
#endif
#define CKSUM "/usr/bin/cksum"
#define UNIQ "/usr/bin/uniq"

#define NODE_LIST "node_list"
#define MULTIQUERY "multiquery"
#define MULTICOPY "multicopy"

typedef struct Node {
  NodeReply *n_reply;
} Node;

typedef struct File {
  char *f_name;
} File;

static File files[MAX_FILES];
static int numFiles;

static Node nodes[MAX_NODES];
static int numNodes;

HANDLE hdebugLog = NULL;

static char tempfileName[256];
/*-----------------------------------------------------------------*/
static void
ScanGrep(char *name)
{
  char command[512];
  char result[512];
  FILE *f;
  int numAccounted = 0;
  int i;

  sprintf(command, "grep '\\ %s$' %s3", name, tempfileName);
  if ((f = popen(command, "r")) == NULL) {
    fprintf(stderr, "grep failed\n");
    exit(-1);
  }

  while (fgets(result, sizeof(result), f) != NULL) {
    int numThis = atoi(result);
    if (numThis > numNodes) {
      fprintf(stderr, "sanity failed - count too high\n");
      exit(-1);
    }
    else if (numThis == numNodes) {
      /* all present, do nothing */
      pclose(f);
      return;
    }
    if (numAccounted == 0)
      printf("\nfile %s\n", name);
    numAccounted += numThis;
    if (numThis > numNodes/2) {
      printf("\tmajority: %s", result);
    }
    else {
      char testString[64];
      printf("\tminority: %s", result);
      sprintf(testString, "%s", GetWord(result, 1));
      for (i = 0; i < numNodes; i++) {
	if (strstr(nodes[i].n_reply->nr_buf, testString) != NULL)
	  printf("\t\t%s\n", nodes[i].n_reply->nr_name);
      }
    }
  }

  if (numAccounted < numNodes) {
    char testString[512];
    sprintf(testString, "%s\n", name);
    printf("\tmissing: %d nodes\n", numNodes - numAccounted);
    for (i = 0; i < numNodes; i++) {
      if (strstr(nodes[i].n_reply->nr_buf, testString) == NULL)
	printf("\t\t%s\n", nodes[i].n_reply->nr_name);
    }
  }
  pclose(f);
}
/*-----------------------------------------------------------------*/
int main(int argc, char *argv[])
{
  FILE *f;
  int i;
  char hostname[256];
  char command[512];
  char *multicopy, *multiquery;
  
  if (gethostname(hostname, sizeof(hostname)) < 0) {
    fprintf(stderr, "could not get host name\n");
    exit(-1);
  }

  sprintf(tempfileName, "temp_%s_%d_", hostname, (int) getpid());

  if ((f = fopen(FILECHECKLIST, "r")) == NULL) {
    fprintf(stderr, "couldn't open %s\n", FILECHECKLIST);
    exit(-1);
  }

  for (i = 0; i < MAX_FILES; i++) {
    char *temp;
    if ((temp = GetNextLine(f)) == NULL) {
      fclose(f);
      break;
    }
    if (numFiles >= MAX_FILES) {
      fprintf(stderr, "too many files\n");
      exit(-1);
    }
    files[i].f_name = temp;
    numFiles = i+1;
  }

  if (numFiles < 1) {
    fprintf(stderr, "couldn't find any files\n");
    exit(-1);
  }

  if ((f = fopen(tempfileName, "w")) == NULL) {
    fprintf(stderr, "couldn't open %s\n", tempfileName);
    exit(-1);
  }
  
  fprintf(f, "echo testing_12456789\n");
  for (i = 0; i < numFiles; i++)
    fprintf(f, "%s %s\n", CKSUM, files[i].f_name);
  fclose(f);

  if (chmod(tempfileName, S_IRUSR | S_IWUSR | S_IXUSR) < 0) {
    fprintf(stderr, "couldn't modify the file mode\n");
    exit(-1);
  }

  putenv("MQ_SLICE=princeton_codeen");
  putenv("MQ_NODES="NODE_LIST);
  putenv("MQ_ORDER=1");
  putenv("MQ_MAXLOAD=3");

  /* copy the file to all nodes */
  if ((multicopy = getenv("MULTICOPY")) == NULL) 
    multicopy = MULTICOPY;
  sprintf(command, "%s %s @: 1>/dev/null 2>&1", multicopy, tempfileName);
  system(command);

  /* execute it on all nodes */
  if ((multiquery = getenv("MULTIQUERY")) == NULL) 
    multiquery = MULTIQUERY;
  sprintf(command, "%s 'sh %s 2>/dev/null'", multiquery, tempfileName);
  if ((f = popen(command, "r")) == NULL) {
    fprintf(stderr, "failed on popen\n");
    exit(-1);
  }

  /* grab all valid replies */
  for (i = 0; i < MAX_NODES; i++) {
    NodeReply *ent;

    if ((ent = NodeReply_GetNext(f)) == NULL)
      break;
    if (ent->nr_bytes < 1)
      continue;

    if (numNodes >= MAX_NODES) {
      fprintf(stderr, "too many nodes\n");
      exit(-1);
    }
    nodes[numNodes].n_reply = ent;
    numNodes++;
  }
  pclose(f);

  if (numNodes < 1) {
    fprintf(stderr, "didn't get any replies\n");
    exit(-1);
  }

  /* write out all replies into single buffer */
  sprintf(command, "%s2", tempfileName);
  if ((f = fopen(command, "w")) == NULL) {
    fprintf(stderr, "couldn't open file 2\n");
    exit(-1);
  }
  for (i = 0; i < numNodes; i++)
    fwrite(nodes[i].n_reply->nr_buf, 1, nodes[i].n_reply->nr_bytes, f);
  fclose(f);

  /* sort buffer, etc */
  sprintf(command, SORT " %s2 | " UNIQ " -c | " SORT " -rn > %s3",
	  tempfileName, tempfileName);
  system(command);

  for (i = 0; i < numFiles; i++)
    ScanGrep(files[i].f_name);

  unlink(tempfileName);
  sprintf(command, "%s2", tempfileName);
  unlink(command);
  sprintf(command, "%s3", tempfileName);
  unlink(command);

  sprintf(command, MULTIQUERY " 'rm %s' 1>/dev/null 2>&1", tempfileName);
  system(command);

  return(0);
}
/*-----------------------------------------------------------------*/
