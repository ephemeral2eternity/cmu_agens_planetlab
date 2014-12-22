#ifndef _GETTIMEOFDAYEX_H_
#define _GETTIMEOFDAYEX_H_
#include <sys/time.h>

int gettimeofdayex(struct timeval *tv, struct timezone *tz);
time_t timeex(time_t *t);

#endif // _GETTIMEOFDAYEX_H_
