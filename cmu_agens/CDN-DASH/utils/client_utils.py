import time
import json
import os
import shutil
import urllib2
import requests
import logging
import socket
import datetime
from monitor.get_hop_info import *
from ipinfo.ipinfo import *

# ================================================================================
## Get Client Agent Name
# ================================================================================
def getMyName():
	hostname = socket.gethostname()

	if '.' not in hostname:
		ext_ip, myInfo = get_ext_ip()
		if "name" in myInfo.keys():
			if '.' in myInfo["name"]:
				hostname = myInfo["name"]
		if ext_ip == "221.199.217.144":
			hostname = "planetlab1.research.nicta.com.au"
		elif ext_ip == "221.199.217.145":
			hostname = "planetlab2.research.nicta.com.au"
		elif ext_ip == "128.2.57.73":
			hostname = "superman.andrew.cmu.edu"

		if '.' not in hostname:
			hostname = ext_ip
	return hostname

## ==================================================================================================
### Setup logger files
## ==================================================================================================
def config_logger():
	client_name = socket.gethostname()
	log_file_path = os.getcwd() + '/log/'
	try:
		os.stat(log_file_path)
	except:
		os.mkdir(log_file_path)

	faults_log_name = log_file_path + 'faults_' + client_name + "_" + datetime.datetime.now().strftime("%d%H%M") + ".log"
	recovery_log_name = log_file_path + 'recovery_' + client_name + "_" + datetime.datetime.now().strftime("%d%H%M") + ".log"
	setup_logger('faults', faults_log_name)
	setup_logger('recovery', recovery_log_name)


## ==================================================================================================
### Setup logger files
## ==================================================================================================
def setup_logger(logger_name, log_file, level=logging.INFO):
	l = logging.getLogger(logger_name)
	formatter = logging.Formatter('%(message)s')
	fileHandler = logging.FileHandler(log_file, mode='w')
	streamHandler = logging.StreamHandler()
	streamHandler.setFormatter(formatter)

	l.setLevel(level)
	l.addHandler(fileHandler)
	l.addHandler(streamHandler)


## ==================================================================================================
# Write JSON file to the dataQoE folder
# @input : json_file_name --- json file name
# 		   json_var --- json variable
## ==================================================================================================
def writeJson(json_file_name, json_var):
	trFolder = os.getcwd() + "/dataQoE/"
	# Create a cache folder locally
	try:
		os.stat(trFolder)
	except:
		os.mkdir(trFolder)

	if json_var:
		trFileName = trFolder + json_file_name + ".json"
		with open(trFileName, 'w') as outfile:
			json.dump(json_var, outfile, sort_keys = True, indent = 4, ensure_ascii=True)


## ==================================================================================================
# Finished steaming videos, write out traces
# @input : client_ID --- the client ID to write traces
# 		   client_tr --- the client trace dictionary
## ==================================================================================================
def writeTrace(client_ID, client_tr):
	trFolder = os.getcwd() + "/dataQoE/"
	# Create a cache folder locally
	try:
		os.stat(trFolder)
	except:
		os.mkdir(trFolder)

	if client_tr:
		trFileName = trFolder + client_ID + ".json"
		with open(trFileName, 'w') as outfile:
			json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

	## If tmp path exists, deletes it.
	if os.path.exists('./tmp'):
		shutil.rmtree('./tmp')

	if os.path.exists(os.getcwd() + "/tmp/"):
		shutil.rmtree(os.getcwd() + "/tmp/")


## ==================================================================================================
# Write 4xx and 5xx HTTP request errors into json file with client name and timestamp
# @input : client_ID --- the client ID to write traces
# 		   error_code_tr --- 4xx and 5xx HTTP request error codes logged with timestamp and client name
## ==================================================================================================
def writeHTTPError(client_ID, error_code_tr):
	if error_code_tr:
		trFolder = os.getcwd() + "/dataQoE/"
		# Create a cache folder locally
		try:
			os.stat(trFolder)
		except:
			os.mkdir(trFolder)
		trFileName = trFolder + client_ID + "_httperr.json"
		with open(trFileName, 'w') as outfile:
			json.dump(error_code_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)


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


## ======================================================================== 
# Log fault messages to client local log files
# @input : client ---- The current client hostname
#		   node ---- The hostname of the impacted node
#		   vidID ---- The impacted video ID
#		   qoe ---- The QoE value the client has due to the fault
#		   fault_type ----- The identifier indicating the type of the fault
#		   msg ---- The content of the error message
## ========================================================================
def local_fault_msg_logger(fault_msg_obj):
	faults_logger = logging.getLogger('faults')
	fault_msg = datetime.datetime.now().strftime("%m%d-%H%M") + ", " + \
				fault_msg_obj['client'] + ", " + fault_msg_obj['node'] + ", " + str(fault_msg_obj['video']) + ", " + \
				"{:2.4f}".format(fault_msg_obj['qoe']) + ", " + str(fault_msg_obj['msg_type']) + ", " + fault_msg_obj['msg']
	faults_logger.info(fault_msg)


## ======================================================================== 
# Log recovery messages to client local log files
# @input : recovery_obj ---- include following keys
#		   'client' ---- The current client hostname
#		   'faulty_node' ---- The node that is faulty and needs to be replaced
#		   'recovery_node' ---- The node that is obtained from other clients via client cooperation
#		   'recovery_peer' ---- The client peer closeby that provides the information for the current client to switch server.
#		   'qoe' ---- The QoE the client experiences with the faulty node
#          'recovery_qoe' ----- The QoE the client is supposed to experience with the recovery node
#		   'vidID' ---- The impacted video ID
#		   'recovery_time' ---- The time period the client takes to recover the fault
#		   'msg' ---- The content of the error message
#		   'fault_type' ----- The identifier of the type of the message
## ========================================================================
def local_recovery_msg_logger(recovery_msg_obj):
	recovery_logger = logging.getLogger('recovery')
	recovery_msg = datetime.datetime.now().strftime("%m%d-%H%M") + ", " + \
				   recovery_msg_obj['client'] + ", " + recovery_msg_obj['faulty_node'] + ", " + recovery_msg_obj['recovery_node'] + ", " + recovery_msg_obj['recovery_peer'] + \
				   ", "  + "{:10.4f}".format(recovery_msg_obj['qoe']) + ", " + "{:10.4f}".format(recovery_msg_obj['recovery_qoe']) + ", " + str(recovery_msg_obj['video']) + \
				   ", "  + "{:10.4f}".format(recovery_msg_obj['recovery_time']) + ", " + str(recovery_msg_obj['msg_type']) + ", " + recovery_msg_obj['msg']
	recovery_logger.info(recovery_msg)
