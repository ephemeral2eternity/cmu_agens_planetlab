#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "parsequery.h"

/*-----------------------------------------------------------------*/
NodeReply *
NodeReply_GetNext(FILE *f)
{
  /* allocates and returns a reply, or else returns NULL */
  char line[1024];
  char *temp;
  NodeReply *reply;

  do {
    if (fgets(line, sizeof(line), f) == NULL)
      return(NULL);
  } while (line[0] == '\n');

  if ((temp = strchr(line , ' ')) == NULL)
    return(NULL);
  if (temp != line && *(temp-1) == ':')
    *(temp-1) = 0;
  *temp++ = 0;			/* now pointing to size */

  if ((reply = calloc(1, sizeof(*reply))) == NULL)
    return(NULL);
  reply->nr_name = strdup(line);

  if (strncmp(temp, "timed out", strlen("timed out")) == 0) {
    reply->nr_bytes = -1;
    return(reply);
  }
  reply->nr_bytes = atoi(temp);

  if (reply->nr_bytes) {
    reply->nr_buf = calloc(1, reply->nr_bytes+1);
    fread(reply->nr_buf, 1, reply->nr_bytes, f);
  }

  return(reply);
}
/*-----------------------------------------------------------------*/
void
NodeReply_Free(NodeReply *reply)
{
  /* frees the given structure */
  if (reply == NULL)
    return;
  if (reply->nr_name != NULL)
    free(reply->nr_name);
  if (reply->nr_buf != NULL)
    free(reply->nr_buf);
  free(reply);
}
/*-----------------------------------------------------------------*/
