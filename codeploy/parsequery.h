#ifndef _PARSEQUERY_H_
#define _PARSEQUERY_H_

#include <stdio.h>

typedef struct NodeReply {
  char *nr_name;		/* name of node */
  int nr_bytes;			/* # bytes, or -1 for timed out */
  char *nr_buf;			/* buffer containing reply */
} NodeReply;

NodeReply *NodeReply_GetNext(FILE *f);
void NodeReply_Free(NodeReply *reply);

#endif /* _PARSEQUERY_H_ */
