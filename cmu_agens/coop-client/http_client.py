import urllib2
import socket
import time
import datetime
import json
import shutil
import os
import logging
from dash_utils import *
from dash_qoe import *
from attach_cache_agent import *
from get_srv import *
from mpd_parser import *
from download_chunk import *
from client_utils import *
from failover import *

## ==================================================================================================
# define the simple client agent that only downloads videos from denoted server
# @input : cache_agent_ip ---- the cache agent that is responsible for monitoring the client
#		   video_srv_ip --- the ip address of the video server
#		   video_name --- the string name of the requested video
## ==================================================================================================
def http_client(cache_agent_ip, srv_info, video_name, bitrate_lvl, period=30):

	## ==================================================================================================
	## Client name and info
	client = str(socket.gethostname())
	cur_ts = time.strftime("%m%d%H%M")
	client_ID = client + "_" + cur_ts + "_simple"

	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts = mpd_parser(srv_info['ip'], video_name)

	### ===========================================================================================================
	## Add mpd_parser failure handler
	### ===========================================================================================================
	trial_time = 0
	while (not rsts) and (trial_time < 10):
		rsts = mpd_parser(srv_info['ip'], video_name)
		trial_time = trial_time + 1

	if not rsts:
		update_qoe(cache_agent_ip, srv_info['ip'], 0, 0.9)
		return

	### ===========================================================================================================
	vidLength = int(rsts['mediaDuration'])
	minBuffer = num(rsts['minBufferTime'])
	reps = rsts['representations']

	# Get video bitrates in each representations
	vidBWs = {}
	for rep in reps:
		if not 'audio' in rep:
			vidBWs[rep] = int(reps[rep]['bw'])		

	sortedVids = sorted(vidBWs.items(), key=itemgetter(1))

	# Start streaming from the denoted bitrate lvl
	vidInit = reps[str(bitrate_lvl)]['initialization']
	maxBW = sortedVids[-1][1]

	# Read common parameters for all chunks
	timescale = int(reps[str(bitrate_lvl)]['timescale'])
	chunkLen = int(reps[str(bitrate_lvl)]['length']) / timescale
	chunkNext = int(reps[str(bitrate_lvl)]['start'])

	## ==================================================================================================
	# Start downloading the initial video chunk
	## ==================================================================================================
	curBuffer = 0
	chunk_download = 0
	loadTS = time.time()
	print "[" + client_ID + "] Start downloading video " + video_name + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
	print "[" + client_ID + "] Selected server for next 12 chunks is :" + srv_info['srv']
	vchunk_sz = download_chunk(srv_info['ip'], video_name, vidInit)
	startTS = time.time()
	print "[" + client_ID + "] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
	est_bw = vchunk_sz * 8 / (startTS - loadTS)
	print "|-- TS --|-- Chunk # --|- Representation -|-- QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|-- Chunk Response Time --|"
	preTS = startTS
	chunk_download += 1
	curBuffer += chunkLen

	## Traces to write out
	client_tr = {}
	srv_qoe_tr = {}
	alpha = 0.1
	

	## ==================================================================================================
	# Start streaming the video
	## ==================================================================================================
	while (chunkNext * chunkLen < vidLength) :
		vidChunk = reps[str(bitrate_lvl)]['name'].replace('$Number$', str(chunkNext))
		loadTS = time.time();
		vchunk_sz = download_chunk(srv_info['ip'], video_name, vidChunk)
		
		## Try 10 times to download the chunk
		error_num = 0
		while (vchunk_sz == 0) and (error_num < 10):
			# Try to download again the chunk
			vchunk_sz = download_chunk(srv_info['ip'], video_name, vidChunk)
			error_num = error_num + 1

		### ===========================================================================================================
		## Failover control for the timeout of chunk request
		### ===========================================================================================================
		if vchunk_sz == 0:
			update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
			return
		else:
			error_num = 0
		### ===========================================================================================================

		curTS = time.time()
		rsp_time = curTS - loadTS
		est_bw = vchunk_sz * 8 / (curTS - loadTS)
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
		curBW = num(reps[str(bitrate_lvl)]['bw'])
		chunk_QoE = computeQoE(freezingTime, curBW, maxBW)

		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", str(bitrate_lvl), "---|---", str(chunk_QoE), "---|---", \
						str(curBuffer), "---|---", str(freezingTime), "---|---", srv_info['srv'], "---|---", str(rsp_time), "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=str(bitrate_lvl), QoE=chunk_QoE, Buffer=curBuffer, \
			Freezing=freezingTime, Server=srv_info['srv'], Response=rsp_time)
		srv_qoe_tr[chunkNext] = chunk_QoE

		# Report QoE every chunk or 30 seconds.
		if chunkLen > period:
			update_qoe(cache_agent_ip, srv_info['srv'], chunk_QoE, alpha)
		else:
			intvl = int(period/chunkLen)
			if chunkNext%intvl == 0:
				mnQoE = averageQoE(srv_qoe_tr, intvl)
				update_qoe(cache_agent_ip, srv_info['srv'], mnQoE, alpha)
			
		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(chunkLen)
		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)

	## If tmp path exists, deletes it.
	if os.path.exists('./tmp'):
		shutil.rmtree('./tmp')

	return