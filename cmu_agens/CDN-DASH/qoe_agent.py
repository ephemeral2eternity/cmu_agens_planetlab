import urllib2
import socket
import time
import datetime
import json
import shutil
import os
import logging
import subprocess
from dash.utils import *
from qoe.dash_chunk_qoe import *
from dash.fault_tolerance import *
from client_utils import *
from communication.post_info import *

## ==================================================================================================
# define the simple client agent that only downloads videos from denoted server
# @input : srv_addr ---- the server name address
#		   video_name --- the string name of the requested video
## ==================================================================================================
def qoe_agent(cdn_host, video_name, locator, update_period=5, qoe_th=1):
	## Define all parameters used in this client
	alpha = 0.5
	retry_num = 10

	## CDN SQS
	CDN_SQS = 5.0
	uniq_srvs = []

	## ==================================================================================================
	# Get Client INFO, streaming configuration file, CDN server and route to the CDN and report the route
	# INFO to the anomaly locator agent
	## ==================================================================================================
	client_ip, client_info = get_ext_ip()
	client = client_info["name"]
	cur_ts = time.strftime("%m%d%H%M")
	client_ID = client + "_" + cur_ts

	rsts, srv_ip = ft_mpd_parser(cdn_host, retry_num, video_name)
	if not rsts:
		return

	## Fork a process doing traceroute to srv_ip and report it to the locator.
	tr_proc = fork_cache_client_info(locator, client_info, srv_ip)

	### ===========================================================================================================
	## Read parameters from dash.mpd_parser
	### ===========================================================================================================
	vidLength = int(rsts['mediaDuration'])
	minBuffer = num(rsts['minBufferTime'])
	reps = rsts['representations']

	# Get video bitrates in each representations
	vidBWs = {}
	for rep in reps:
		if not 'audio' in rep:
			vidBWs[rep] = int(reps[rep]['bw'])
	print vidBWs

	sortedVids = sorted(vidBWs.items(), key=itemgetter(1))

	# Start streaming from the minimum bitrate
	minID = sortedVids[0][0]
	vidInit = reps[minID]['initialization']
	maxBW = sortedVids[-1][1]

	# Read common parameters for all chunks
	timescale = int(reps[minID]['timescale'])
	chunkLen = int(reps[minID]['length']) / timescale
	chunkNext = int(reps[minID]['start'])

	## ==================================================================================================
	# Start downloading the initial video chunk
	## ==================================================================================================
	curBuffer = 0
	chunk_download = 0

	## Traces to write out
	client_tr = {}
	http_errors = {}

	## Download initial chunk
	loadTS = time.time()
	print "[" + client_ID + "] Start downloading video " + video_name + " at " + \
		  datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S") + \
		  " from server : " + cdn_host

	(vchunk_sz, chunk_srv_ip, error_codes) = ft_download_chunk(cdn_host, retry_num, video_name, vidInit)
	http_errors.update(error_codes)
	if vchunk_sz == 0:
		## Write out traces after finishing the streaming
		writeTrace(client_ID + "_cdn", client_tr)
		writeHTTPError(client_ID, http_errors)
		return

	startTS = time.time()
	print "[" + client_ID + "] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
	est_bw = vchunk_sz * 8 / (startTS - loadTS)
	print "|-- TS --|-- Chunk # --|- Representation -|-- Linear QoE --|-- Cascading QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|-- Chunk Response Time --|"
	preTS = startTS
	chunk_download += 1
	curBuffer += chunkLen

	## ==================================================================================================
	# Start streaming the video
	## ==================================================================================================
	while (chunkNext * chunkLen < vidLength):
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)
		vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkNext))
		loadTS = time.time()
		(vchunk_sz, chunk_srv_ip, error_codes) = ft_download_chunk(cdn_host, retry_num, video_name, vidChunk)

		# If the client changes servers, get the traceroute to the new server.
		if chunk_srv_ip != srv_ip:
			srv_ip = chunk_srv_ip
			## Fork a process doing traceroute to srv_ip and report it to the locator.
			fork_cache_client_info(locator, client_info, srv_ip)

		http_errors.update(error_codes)
		if vchunk_sz == 0:
			## Write out traces after finishing the streaming
			writeTrace(client_ID, client_tr)
			writeHTTPError(client_ID, http_errors)
			return

		curTS = time.time()
		rsp_time = curTS - loadTS
		est_bw = vchunk_sz * 8 / rsp_time
		time_elapsed = curTS - preTS

		# Compute freezing time
		if time_elapsed > curBuffer:
			freezingTime = time_elapsed - curBuffer
			curBuffer = 0
		# print "[AGENP] Client freezes for " + str(freezingTime)
		else:
			freezingTime = 0
			curBuffer = curBuffer - time_elapsed

		# Compute QoE of a chunk here
		curBW = num(reps[nextRep]['bw'])
		chunk_linear_QoE = computeLinQoE(freezingTime, curBW, maxBW)
		chunk_cascading_QoE = computeCasQoE(freezingTime, curBW, maxBW)

		CDN_SQS = (1 - alpha) * CDN_SQS + alpha * chunk_cascading_QoE
		print CDN_SQS

		# print "Chunk Size: ", vchunk_sz, "estimated throughput: ", est_bw, " current bitrate: ", curBW

		print "|---", str(curTS), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_linear_QoE), "---|---", \
			str(chunk_cascading_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", chunk_srv_ip, "---|---", str(rsp_time), "---|"

		client_tr[chunkNext] = dict(TS=curTS, Representation=nextRep, QoE1=chunk_linear_QoE, QoE2=chunk_cascading_QoE, Buffer=curBuffer, \
									Freezing=freezingTime, Server=chunk_srv_ip, Response=rsp_time)

		if chunk_srv_ip not in uniq_srvs:
			uniq_srvs.append(chunk_srv_ip)

		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(curBuffer - 30)

		## Update route info periodically
		if chunk_cascading_QoE > qoe_th:
			if (chunkNext % update_period == 0) and (chunkNext > 0):
				isUpdated = updateRoute(locator, client_ip, srv_ip)
				if isUpdated:
					print "Updated the status of route successfully!"
				else:
					print "Failed to update the status of the existing route!"
		else:
			print "Please add anomaly localization request here!"

		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)
	if http_errors:
		writeTrace(client_ID + "_httperr", http_errors)

	tr_proc.join(timeout=100)
	return client_ID, CDN_SQS, uniq_srvs
