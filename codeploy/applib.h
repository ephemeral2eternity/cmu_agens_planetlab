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
 * $Id: applib.h,v 1.19 2004/03/13 04:59:10 vivek Exp $
 */

#ifndef _APPLIB_H_
#define _APPLIB_H_

#include <stdio.h>
#include <sys/time.h>

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif

#ifndef SUCCESS
#define SUCCESS 0
#endif

#ifndef FAILURE
#define FAILURE (-1)
#endif

float DiffTimeVal(struct timeval *start, struct timeval *end);

int CreatePrivateAcceptSocket(int portNum, int nonBlocking);
int CreatePublicUDPSocket(int portNum);
int MakeLoopbackConnection(int portNum, int nonBlocking);
char *GetField(const unsigned char *start, int whichField);
char *GetWord(const unsigned char *start, int whichWord);

int Base36Digit(int a);
int Base36To10(int a);
int PopCount(int val);
int PopCountChar(int val);
int LogValChar(int val);

const char *StringOrNull(const char *s);
char *strchars(const char *string, const char *list);
char *strnstr(const char * s1, int s1_len, const char * s2);
char *StrdupLower(const char *orig);
void StrcpyLower(char *dest, const char *src);
void StrcpyLowerExcept(char *dest, int dest_max, const char* src, const char* except);
char *GetLowerNextLine(FILE *file);
char *GetNextLine(FILE *file);
int DoesSuffixMatch(char *start, int len, char *suffix);

#ifndef __APPLE__
#include <alloca.h>
#endif
#include <string.h>

/*  allocate stack memory to copy "src" to "dest" in lower cases */
#define LOCAL_STR_DUP_LOWER(dest, src)    \
  { dest = alloca(strlen(src) + 1);       \
    StrcpyLower(dest, src);               \
  }
  
/*  allocate stack memory to copy "src" to "dest" */
#define LOCAL_STR_DUP(dest, src)         \
  { dest = alloca(strlen(src) + 1);      \
    strcpy(dest, src);                   \
  }

/* release memory pointer after checking NULL */
#define FREE_PTR(x) if ((x) != NULL) { free(x);}

/* Bit vector implementation */
void SetBits(int* bits, int idx, int maxNum);
int GetBits(int* bits, int idx, int maxNum);
int GetNumBits(int* bitvecs, int maxNum);

/* extended logging */
typedef void* HANDLE;             

HANDLE CreateLogFHandle(const char* signature, int change_file_name_on_save);
int OpenLogF(HANDLE file);
int WriteLog(HANDLE file, const char* data, int size, int forceFlush);
void DailyReopenLogF(HANDLE file);

/* flush the buffer */
#define FlushLogF(h)  WriteLog(h, NULL, 0, TRUE)

/* maximum single log file size, defined in applib.c */
extern int maxSingleLogSize; 

#ifdef __sparc
#define timeex(a) time(a)
#else
#include "gettimeofdayex.h"
#endif

#endif
