import time
import json
import os
import shutil

## ==================================================================================================
# Finished steaming videos, write out traces
# @input : client_ID --- the client ID to write traces
# 		   client_tr --- the client trace dictionary
## ==================================================================================================
def writeTrace(client_ID, client_tr):
	trFileName = "./dataQoE/" + client_ID + ".json"
	with open(trFileName, 'w') as outfile:
		json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

	## If tmp path exists, deletes it.
	if os.path.exists('./tmp'):
		shutil.rmtree('./tmp')

## ==================================================================================================
# Write out Error Client Traces
# @input : client_ID --- the client ID to write traces
## ==================================================================================================
def reportErrorQoE(client_ID, srv=None, trace=None):
	client_tr = {}
	curTS = time.time()
	if trace:
		client_error_ID = "crash_" + client_ID
		writeTrace(client_error_ID, trace)

	client_tr["0"] = dict(TS=int(curTS), QoE=0, Server=srv, Representation=-1, Freezing=-1, Response=1000, Buffer=0)
	writeTrace(client_ID, client_tr)