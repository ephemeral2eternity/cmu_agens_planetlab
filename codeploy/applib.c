/*
 * Copyright (c) 1999-2000
 * by iMimic Networking, Inc., Houston, Texas
 *
 * This software is furnished under a license and may be used and copied only
 * in accordance with the terms of such license and with the inclusion of the
 * above copyright notice.  This software or any other copies thereof may not
 * be provided or otherwise made available to any other person.  No title to
 * or ownership of the software is hereby transferred.
 *
 * $Id: applib.c,v 1.20 2004/03/05 03:13:14 kyoungso Exp $
 */

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <ctype.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "applib.h"
#include "debug.h"

/*-----------------------------------------------------------------*/
float
DiffTimeVal(struct timeval *start, struct timeval *end)
{
  return(end->tv_sec - start->tv_sec + 
	 1e-6*(end->tv_usec - start->tv_usec));
}
/*-----------------------------------------------------------------*/
int
CreatePrivateAcceptSocket(int portNum, int nonBlocking)
{
  int doReuse = 1;
  struct linger doLinger;
  int sock;
  struct sockaddr_in sa;
  
  /* Create socket. */
  if ((sock = socket(PF_INET, SOCK_STREAM, 0)) == -1)
    return(-1);
  
  /* don't linger on close */
  doLinger.l_onoff = doLinger.l_linger = 0;
  if (setsockopt(sock, SOL_SOCKET, SO_LINGER, 
		 &doLinger, sizeof(doLinger)) == -1) {
    close(sock);
    return(-1);
  }
  
  /* reuse addresses */
  if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, 
		 &doReuse, sizeof(doReuse)) == -1) {
    close(sock);
    return(-1);
  }

  if (nonBlocking) {
    /* make listen socket nonblocking */
    if (fcntl(sock, F_SETFL, O_NDELAY) == -1) {
      close(sock);
      return(-1);
    }
  }
  
  /* set up info for binding listen */
  memset(&sa, 0, sizeof(sa));
  sa.sin_family = AF_INET;
  sa.sin_addr.s_addr = htonl(INADDR_ANY);
  sa.sin_port = htons(portNum);

  /* bind the sock */
  if (bind(sock, (struct sockaddr *) &sa, sizeof(sa)) == -1) {
    close(sock);
    return(-1);
  }
  
  /* start listening */
  if (listen(sock, 32) == -1) {
    close(sock);
    return(-1);
  }
  
  return(sock);
}
/*-----------------------------------------------------------------*/
int
CreatePublicUDPSocket(int portNum)
{
  struct sockaddr_in hb_sin;
  int sock;

  if ((sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0)
    return(-1);

  memset(&hb_sin, 0, sizeof(hb_sin));
  hb_sin.sin_family = AF_INET;
  hb_sin.sin_addr.s_addr = INADDR_ANY;
  hb_sin.sin_port = htons(portNum);

  if (bind(sock, (struct sockaddr *) &hb_sin, sizeof(hb_sin)) < 0) {
    close(sock);
    return(-1);
  }
  return(sock);
}
/*-----------------------------------------------------------------*/
int
MakeLoopbackConnection(int portNum, int nonBlocking)
{
  struct sockaddr_in saddr;
  int fd;

  if ((fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0)
    return(-1);

  if (nonBlocking) {
    if (fcntl(fd, F_SETFL, O_NDELAY) < 0) {
      close(fd);
      return(-1);
    }
  }

  saddr.sin_family = AF_INET;
  saddr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  saddr.sin_port = htons(portNum);
  
  if (connect(fd, (struct sockaddr *) &saddr, 
	      sizeof(struct sockaddr_in)) < 0) {
    close(fd);
    return(-1);
  }

  return(fd);
}
/*-----------------------------------------------------------------*/
char *
GetField(const unsigned char *start, int whichField)
{
  int currField;

  /* move to first non-blank char */
  while (isspace(*start))
    start++;

  if (*start == '\0')
    return(NULL);

  for (currField = 0; currField < whichField; currField++) {
    /* move over this field */
    while (*start != '\0' && (!isspace(*start)))
      start++;
    /* move over blanks before next field */
    while (isspace(*start))
      start++;
    if (*start == '\0')
      return(NULL);
  }
  return((char *) start);
}
/* ---------------------------------------------------------------- */
char *
GetWord(const unsigned char *start, int whichWord)
{
  /* returns a newly allocated string containing the desired word,
     or NULL if there was a problem */
  unsigned char *temp;
  int len = 0;
  char *res;

  temp = (unsigned char *) GetField(start, whichWord);
  if (!temp)
    return(NULL);
  while (!(temp[len] == '\0' || isspace(temp[len])))
    len++;
  if (!len) {
    TRACE("internal error\n");
    exit(-1);
  }
  res = calloc(1, len+1);
  if (!res) {
    TRACE("out of memory\n");
    exit(-1);
  }
  memcpy(res, temp, len);
  return(res);
}
/*-----------------------------------------------------------------*/
int
Base36Digit(int a)
{
  if (a < 0)
    return('0');
  if (a > 35)
    return('z');
  if (a < 10)
    return('0' + a);
  return('a' + a-10);
}
/*-----------------------------------------------------------------*/
int
Base36To10(int a)
{
  if (a >= '0' && a <= '9')
    return(a - '0');
  if (a >= 'a' && a <= 'z')
    return(10 + a - 'a');
  if (a >= 'A' && a <= 'Z')
    return(10 + a - 'A');
  return(0);
}
/*-----------------------------------------------------------------*/
int
PopCount(int val)
{
  int i;
  int count = 0;

  for (i = 0; i < sizeof(int) * 8; i++) {
    if (val & (1<<i))
      count++;
  }
  return(count);
}
/*-----------------------------------------------------------------*/
int
PopCountChar(int val)
{
  int i;
  int count = 0;

  for (i = 0; i < sizeof(int) * 8; i++) {
    if (val & (1<<i))
      count++;
  }
  return(Base36Digit(count));
}
/*-----------------------------------------------------------------*/
int
LogValChar(int val)
{
  int i;

  for (i = 0; i < 32; i++) {
    if (val <= (1<<i))
      return(Base36Digit(i));
  }
  return(Base36Digit(32));
}
/*-----------------------------------------------------------------*/
const char *
StringOrNull(const char *s)
{
  if (s)
    return(s);
  return("(null)");
}
/*-----------------------------------------------------------------*/
char *
strchars(const char *string, const char *list)
{
  /* acts like strchr, but works with multiple characters */
  int numChars = strlen(list);
  int i;
  const char *walk;

  if (numChars < 1)
    return(NULL);
  
  for (walk = string; *walk; walk++) {
    for (i = 0; i < numChars; i++) {
      if (*walk == list[i])
	return (char *)(walk);
    }
  }
  return(NULL);
}

/* same as strstr, except that si doesn't have to end at '\0' */
char * strnstr(const char * s1, int s1_len, const char * s2)
{
	int l1, l2;

	l2 = strlen(s2);
	if (!l2)
	  return (char *) s1;

	l1 = s1_len;
	while (l1 >= l2) {
		l1--;
		if (!memcmp(s1,s2,l2))
		  return (char *) s1;
		s1++;
	}
	return NULL;
}

/*-----------------------------------------------------------------*/
char *
StrdupLower(const char *orig)
{
  char *temp;
  int i;

  if ((temp = strdup(orig)) == NULL) {
    TRACE("no memory in strduplower\n");
    exit(-1);
  }
  for (i = 0; temp[i]; i++) {
    if (isupper((int) temp[i]))
      temp[i] = tolower(temp[i]);
  }
  return(temp);
}

/*-----------------------------------------------------------------*/
void 
StrcpyLower(char *dest, const char *src)
{
  /* copy 'src' to 'dest' in lower cases. 
     'dest' should have enough free space to hold src */
  int i;

  for (i = 0; src[i]; i++) {
    dest[i] = (isupper((int) src[i])) ? tolower(src[i]) : src[i];
  }

  /* mark it as NULL */
  dest[i] = 0;
}
/*-----------------------------------------------------------------*/
void
StrcpyLowerExcept(char *dest, int dest_max, const char* src, const char* except)
{
  /* copy 'src' to 'dest' in lower cases, skipping the chars in except.
     'dest' should have enough free space to hold src */
  int i, j;

  if (src == NULL)
    return;
  
  for (i = 0, j= 0; src[i]; i++) {
    if (strchr(except, src[i]))
      continue;

    if (j == dest_max - 1)
      break;
    dest[j++] = (isupper((int) src[i])) ? tolower(src[i]) : src[i];
  }

  /* mark it as NULL */
  dest[j] = 0;
}

/*-----------------------------------------------------------------*/
static char *
GetNextLineBack(FILE *file, int lower)
{
  /* reads the next non-blank line of the file. strips off any leading
     space, any comments, and any trailing space.  returns a lowercase
     version of the line that has been malloc'd */
  char line[1024];

  while (fgets(line, sizeof(line), file) != NULL) {
    char *temp;
    int len;

    /* strip off any comments, leading and trailing whitespace */
    if ((temp = strchr(line, '#')) != NULL)
      *temp = 0;
    len = strlen(line);
    while (len > 0 && isspace((int) line[len-1])) {
      len--;
      line[len] = 0;
    }
    temp = line;
    while (isspace((int) *temp))
      temp++;
    if (temp[0] == 0)
      continue;			/* blank line, move on */

    if (lower)
      return(StrdupLower(temp));
    return(strdup(temp));
  }

  return(NULL);
}
/*-----------------------------------------------------------------*/
char *
GetLowerNextLine(FILE *file)
{
  return(GetNextLineBack(file, TRUE));
}
/*-----------------------------------------------------------------*/
char *
GetNextLine(FILE *file)
{
  return(GetNextLineBack(file, FALSE));
}
/*-----------------------------------------------------------------*/
int
DoesSuffixMatch(char *start, int len, char *suffix)
{
  int sufLen = strlen(suffix);

  if (len < 1)
    len = strlen(start);
  if (len < sufLen)
    return(FALSE);
  if (strncasecmp(start+len-sufLen, suffix, sufLen))
    return(FALSE);
  return(TRUE);
}

/*-----------------------------------------------------------------*/
/*                                                                 */
/* Bit Vector Implementation                                       */
/*                                                                 */
/*-----------------------------------------------------------------*/
#define BIT_INDEX (0x0000001F)

void
SetBits(int* bits, int idx, int maxNum)
{
  if (idx > (maxNum << 5)) {
    TRACE("Invalid index: %d", idx);
    return;
  }
  bits[(idx >> 5)] |= (1 << (idx & BIT_INDEX));
}
/*-----------------------------------------------------------------*/
int
GetBits(int* bits, int idx, int maxNum)
{
  if (idx > (maxNum << 5)) {
    TRACE("Invalid index: %d", idx);
    return FALSE;
  }
  return (bits[(idx >> 5)] & (1 << (idx & BIT_INDEX)));
}

/*-----------------------------------------------------------------*/
static inline int
GetNumBits_I(int bitvec)
{
  int i, count;

  for (i = 0, count = 0; i < 32; i++)
    if (bitvec & (1 << i)) count++;
  return count;
}

/*-----------------------------------------------------------------*/
int 
GetNumBits(int* bitvecs, int maxNum)
{
  int i, count;

  /* get the number of bits that have been set to 1 */
  for (i = 0, count = 0; i < maxNum; i++)
    count += GetNumBits_I(bitvecs[i]);
  return count;
}

/*-----------------------------------------------------------------*/

/* Logging & Trace support */

/* buffer threshold : when the size hits this value, it flushes its content
   to the file  */
#define LOG_BYTES_THRESHOLD (32*1024)

/* this flag indicates that it preserves the base file name for the current
   one, and changes its name when it actually closes it off */
#define CHANGE_FILE_NAME_ON_SAVE 0x01 

/* size of the actual log buffer */
#define LOG_BYTES_MAX       (2*LOG_BYTES_THRESHOLD)

/* log/trace book keeping information */
typedef struct ExtendedLog {
  char buffer[LOG_BYTES_MAX]; /* 64 KB */
  int  bytes;           /* number of bytes written */
  int  filesize;        /* number of bytes written into this file so far */
  int  fd;              /* file descriptor */
  char* sig;            /* base file name */
  int flags;            /* flags */
  time_t nextday;
} ExtendedLog, *PExtendedLog;

/* maximum single file size */
int maxSingleLogSize = 100 * (1024*1024);

static time_t
GetNextLogFileName(char* file, int size, const char* sig)
{
#define COMPRESS_EXT ".bz2"

  struct tm cur_tm;
  time_t cur_t;
  int idx = 0;

  cur_t = timeex(NULL);
  cur_tm = *gmtime(&cur_t);

  for (;;) {
    /* check if .bz2 exists */
    snprintf(file, size, "%s.%04d%02d%02d_%03d%s", 
	     sig, cur_tm.tm_year+1900, cur_tm.tm_mon+1, cur_tm.tm_mday, 
	     idx++, COMPRESS_EXT);

    if (access(file, F_OK) == 0) 
      continue;

    /* strip the extension and see if the (uncompressed) file exists */
    file[strlen(file) - sizeof(COMPRESS_EXT) + 1] = 0;
    if (access(file, F_OK) != 0)
      break;
  }
  
  /* calculate & return the next day */
  cur_t -= (3600*cur_tm.tm_hour + 60*cur_tm.tm_min + cur_tm.tm_sec);
  return cur_t + 60*60*24;

#undef COMPRESS_EXT
}

/*-----------------------------------------------------------------*/
static void
FlushBuffer(HANDLE file) 
{
  /* write data into the file */
  ExtendedLog* pel = (ExtendedLog *)file;
  int written;

  if (pel == NULL || pel->fd < 0)
    return;
  
  if ((written = write(pel->fd, pel->buffer, pel->bytes)) > 0) {
    pel->bytes -= written;

    /* if it hasn't written all data, then we need to move memory */
    if (pel->bytes > 0) 
      memmove(pel->buffer, pel->buffer + written, pel->bytes);
    pel->buffer[pel->bytes] = 0;
    pel->filesize += written;
  }
  
  /* if the filesize is bigger than maxSignleLogSize, then close it off */
  if (pel->filesize >= maxSingleLogSize) 
    OpenLogF(file);
}

/*-----------------------------------------------------------------*/
HANDLE
CreateLogFHandle(const char* signature, int change_file_name_on_save)
{
  ExtendedLog* pel;

  if ((pel = (ExtendedLog *)calloc(1, sizeof(ExtendedLog))) == NULL) {
    TRACE("failed");
    exit(-1);
  }

  pel->fd = -1;
  pel->sig = strdup(signature);
  if (pel->sig == NULL) {
    TRACE("signature copying failed\n");
    exit(-1);
  }
  if (change_file_name_on_save)
    pel->flags |= CHANGE_FILE_NAME_ON_SAVE;

  return pel;
}


/*-----------------------------------------------------------------*/
int
OpenLogF(HANDLE file)
{
  char filename[1024];
  ExtendedLog* pel = (ExtendedLog *)file;

  if (pel == NULL)
    return -1;

  if (pel->fd != -1) 
    close(pel->fd);

  pel->nextday = GetNextLogFileName(filename, sizeof(filename), pel->sig);

  /* change the file name only at saving time 
     use pel->sig as current file name         */
  if (pel->flags & CHANGE_FILE_NAME_ON_SAVE) {
    if (access(pel->sig, F_OK) == 0) 
      rename(pel->sig, filename);
    strcpy(filename, pel->sig);
  }

  /* file opening */
  if ((pel->fd = open(filename, O_RDWR | O_CREAT | O_APPEND, 
		      S_IRUSR | S_IWUSR)) == -1) {
    fprintf(stderr, "couldn't open the extended log file\n");
    exit(-1);
  }

  /* reset the file size */
  pel->filesize = 0;
  return 0;
}

/*-----------------------------------------------------------------*/
int 
WriteLog(HANDLE file, const char* data, int size, int forceFlush)
{
  ExtendedLog* pel = (ExtendedLog *)file;

  /* if an error might occur, then stop here */
  if (pel == NULL || pel->fd < 0 || size > LOG_BYTES_MAX)
    return -1;

  if (data != NULL) {
    /* flush the previous data, if this data would overfill the buffer */
    if (pel->bytes + size >= LOG_BYTES_MAX) 
      FlushBuffer(file);

    /* write into the buffer */
    memcpy(pel->buffer + pel->bytes, data, size);
    pel->bytes += size;
  }

  /* need to flush ? */
  if ((forceFlush && (pel->bytes > 0)) || (pel->bytes >= LOG_BYTES_THRESHOLD))
    FlushBuffer(file);

  return 0;
}

/*-----------------------------------------------------------------*/
void
DailyReopenLogF(HANDLE file) 
{
  /* check if current file is a day long,
     opens another for today's file         */
  ExtendedLog* pel = (ExtendedLog *)file;

  if (pel && (timeex(NULL) >= pel->nextday)) {
    FlushLogF(file);               /* flush */
    OpenLogF(file);                /* close previous one & reopen today's */
  }
}
