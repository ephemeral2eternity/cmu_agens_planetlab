#
#  Copyright (c) 1999-2001
#  by iMimic Networking, Inc., Houston, Texas
# 
#  This software is furnished under a license and may be used and copied only
#  in accordance with the terms of such license and with the inclusion of the
#  above copyright notice.  This software or any other copies thereof may not
#  be provided or otherwise made available to any other person.  No title to
#  or ownership of the software is hereby transferred.
# 
#  $Id: Makefile,v 1.10 2004/03/30 19:10:12 vivek Exp $
#

# OSSPECCFLAGS ?= -mpreferred-stack-boundary=2 -march=i686

CFLAGS	=  -DNON_API_ONLY -Wall -Wshadow -Wunused -g -O -I/usr/local/include $(OSSPECCFLAGS)
CC = gcc

MQ_OBJS = multiquery.o applib.o gettimeofdayex.o
NS_OBJS = nodesumm.o parsequery.o applib.o gettimeofdayex.o
FC_OBJS = filecheck.o parsequery.o applib.o gettimeofdayex.o
OBJS = $(MQ_OBJS) $(NS_OBJS) $(FC_OBJS)

LIBS = -lm

CODE =  applib.c filecheck.c gettimeofdayex.c multiquery.c parsequery.c

HDRS =  applib.h debug.h gettimeofdayex.h parsequery.h

SRCS = $(CODE) $(HDRS)

APPS = multiquery multicopy filecheck

all: $(APPS)

multiquery: $(MQ_OBJS)
	${CC} ${CFLAGS} -o multiquery $(MQ_OBJS) $(LIBS) -lm 

multicopy: $(MQ_OBJS)
	${CC} ${CFLAGS} -o multicopy $(MQ_OBJS) $(LIBS) -lm 

filecheck: $(FC_OBJS)
	${CC} ${CFLAGS} -o filecheck $(FC_OBJS) $(LIBS) -lm 

clean:
	rm -f $(OBJS)  *~ *.core .depend
	/bin/touch -t 197001010000 .depend 

cleanall: clean
	rm -r $(APPS)

depend: .depend

.depend: $(SRCS)
	${CC} ${CFLAGS} -MM $(CODE) > .depend

include .depend
