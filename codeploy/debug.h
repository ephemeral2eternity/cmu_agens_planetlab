#ifndef _DEBUG_H_
#define _DEBUG_H_
#include <stdio.h>
#include "applib.h"

/*
  TRACE  : print with function name
  TRACE0 : print without function name
  TRACE1 : print "buf" whose size is "size"
*/

#define DEBUG

extern HANDLE hdebugLog;
#define TRACE0(fmt, msg...) {                                 \
       char __buf[2048];                                      \
       snprintf(__buf, sizeof(__buf), fmt, ##msg);            \
       WriteLog(hdebugLog, __buf, strlen(__buf), TRUE);       \
}          
#define TRACE1(buf, size) {                     \
       WriteLog(hdebugLog, buf, size, TRUE);    \
}
#define TRACE(fmt, msg...) {                                             \
       char __buf[2048];                                                 \
       snprintf(__buf, sizeof(__buf), "[%s] " fmt, __FUNCTION__, ##msg); \
       WriteLog(hdebugLog, __buf, strlen(__buf), TRUE);                  \
}                                                                  

#ifndef HERE
#define HERE TRACE("file %s, line %d, func %s\n",  __FILE__, __LINE__, __FUNCTION__)
#endif

#ifdef DEBUG
#define ASSERT(exp) {                                         \
  if (!(exp)) {                                               \
    TRACE("ASSERTION (%s) FAILED in %s (%s:%d)\n",            \
	 (#exp), __FUNCTION__, __FILE__, __LINE__);           \
  }                                                           \
}
#else
#define ASSERT(exp)         1 ? (void)0 : (exp)
#endif // DEBUG

#endif
