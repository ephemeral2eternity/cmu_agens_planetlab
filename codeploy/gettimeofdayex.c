#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <sys/types.h>
#include <sys/unistd.h>
#include <stdlib.h>
#include <string.h>
#include "gettimeofdayex.h"

/* Macros */
#define rdtsc(low, high) \
   asm volatile("rdtsc":"=a" (low), "=d" (high))

/* get cycle counts */
#define GET_CC(cc)                       \
do                                       \
{                                        \
   cc = 0;                               \
   unsigned long __cc_low__,__cc_high__; \
   rdtsc(__cc_low__,__cc_high__);        \
   cc = __cc_high__;                     \
   cc = (cc << 32) + __cc_low__;         \
}                                        \
while(0)

/*-------------------------------------------------------------------------*/
static int
get_cpu_speed(double* cpu_speed) 
{
   FILE* fp = NULL;
   char  *line = NULL;
   size_t len = 0;
   ssize_t num;
   char* ptr  = 0;

   if (cpu_speed == NULL) 
     return -1;

   if ((fp = fopen("/proc/cpuinfo", "r")) == NULL) 
     return -1;

   while ((num = getline(&line, &len, fp)) != -1) {
      ptr = strtok(line, ":\n");
      if (ptr && strstr(ptr, "cpu MHz")) {
         ptr = strtok(0," \r\t\n");
         *cpu_speed = strtod(ptr, 0);
	 break;
      }
   }
   if (line) 
     free(line);

   fclose(fp);
   return (*cpu_speed == 0) ? -1 : 0;
}

/*--------------------------------------------------------------------------*/
int 
gettimeofdayex(struct timeval *tv, struct timezone *tz)
{
#define MAX_64_BIT_NUM ((unsigned long long)(-1))

  /* TO DO: timezone adjustment */
  static int first = 1, impossible = 0;
  static double cpu_speed;
  static struct timeval start;
  static unsigned long long cc_start;
  unsigned long long cc_now, cc_diff, usec;

  /* initialize : get the current time 
     and fix it as a starting point */
  if (first) {
    if (get_cpu_speed(&cpu_speed) < 0)
      impossible = 1;

    GET_CC(cc_start);
    gettimeofday(&start, 0);
    if (tv)
      *tv = start;
    first = 0;
    return 0;
  }

  /* if it's impossible to get cycle counts, 
     then use original gettimeofday() */
  if (impossible)
    return gettimeofday(tv, tz);

  if (tv) {
    GET_CC(cc_now);

    /* when overflow happens, we need to take care of the carry bit,
       otherwise we get wrong result since we are using unsigned variables.
       assuming cycle counter starts from zero at time zero,
       this would happen after 136 years on 4GHz CPU.
       however, lets just play on the safer side.
    */

    cc_diff = (cc_now < cc_start) ? cc_now + (MAX_64_BIT_NUM - cc_start)
                                  : cc_now - cc_start;
    usec = (unsigned long long)(cc_diff / cpu_speed);

    *tv = start;
    tv->tv_sec  += (usec / 1000000);
    tv->tv_usec += (usec % 1000000);

    if (tv->tv_usec >= 1e6) {
      tv->tv_sec++;
      tv->tv_usec -= 1e6;
    }
  }

  return 0;
}

/*--------------------------------------------------------------------------*/
time_t 
timeex(time_t *t)
{
  /* simple version of time() */
  struct timeval s;

  gettimeofdayex(&s, NULL);
  if (t)
    *t = (time_t)s.tv_sec;

  return (time_t)s.tv_sec;
}
