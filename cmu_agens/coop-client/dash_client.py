## coop_client.py
# The cooperative client agent that achieves fault tolerance and fault detection via exchanging messages
# with peer clients close to each other and peer clients streaming videos from the same server.
## Chen Wang, July 22, 2014, chenw@cmu.edu
import urllib2
import socket
import time
import datetime
import json
import shutil
import os
import logging
import sqlite3 as lite
from dash_utils import *
from dash_qoe import *
from attach_cache_agent import *
from get_srv import *
from get_peer import *
from mpd_parser import *
from download_chunk import *
from client_utils import *
from coop_utils import *
from failover import *
from cooperation import *
from cfds_logger_utils import *

## ==================================================================================================
# Define dash_client method that streams a video using common dash player with general server selection
# method in CDN
# @input : cache_agent_obj --- the dict denoting cache agent ip and name
#		   video_id --- the video id the client is requesting
#		   method --- determine the fault tolerance solution of the client
#						
## ==================================================================================================
def dash_client(cache_agent_obj, video_id, method, expID=None, DASH_PERIOD=6):

	## ==================================================================================================
	## Client name and info
	client = str(socket.gethostname())
	if expID:
		client_ID = client + "_" + expID + "_" + method
	else:
		cur_ts = time.strftime("%m%d%H%M")
		client_ID = client + "_" + cur_ts + "_" + method

	## ==================================================================================================
	## Get the initial streaming server
	srv_info = get_srv(cache_agent_obj['ip'], video_id, method)

	## The cache agent does not give a server for streaming
	## Try to change the cache agent by cooperating with closeby peers.
	#if not srv_info:
	#	cache_agent_obj, srv_info = ft_cache_agent(cache_agent_obj, video_id)

	## ==================================================================================================
	## Get closeby clients from the closest cache agent.
	## We by default assume the p_peers list will be obtained if cache agent is on.
	#p_peers = get_peers(cache_agent_obj['ip'], "pclient")
	#if not p_peers:
	#	p_peers = ft_pv_peers(cache_agent_obj['ip'], "pclient")

	## Get peer client from the streaming server. We by default assume the v_peers list will be obtained
	# if the cache agent on this streaming server is on.
	# If our agent is not running, we report the error directly as redirector fault.
	#v_peers = get_peers(srv_info['ip'], "vclient")
	#if not v_peers:
	#	v_peers = ft_pv_peers(srv_info['ip'], "vclient") 

	## ==================================================================================================
	## Parse the mpd file for the streaming video
	videoName = srv_info['vidName']

	## Debugging the bw issue
	#srv_info['vidName'] = 'BBB'
	#videoName = 'BBB'

	rsts = mpd_parser(srv_info['ip'], videoName)

	## Add mpd_parser failure handler
	#if not rsts:
		## If the client can not download the mpd file for the video, the server is probably down or there
		# might be byzantine faults where
	#	[srv_info, rsts] = coop_ft_srv_mpd(cache_agent_obj['ip'], srv_info, video_id, v_peers, p_peers)

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
	loadTS = time.time()
	print "[" + client_ID + "] Start downloading video " + videoName + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
	print "[" + client_ID + "] Selected server for next 12 chunks is :" + srv_info['srv']
	vchunk_sz = download_chunk(srv_info['ip'], videoName, vidInit)
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
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)
		vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkNext))
		loadTS = time.time();
		vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
		
		## Try 10 times to download the chunk
		error_num = 0
		while (vchunk_sz == 0) and (error_num < 2):
			# Try to download again the chunk
			vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
			error_num = error_num + 1

		### ===========================================================================================================
		## Client Cooperation based Fault Tolerance the timeout of chunk request
		### ===========================================================================================================
		#if vchunk_sz == 0:
		#	logging.info("[" + client_ID + "]Agens client can not download chunks video " + videoName + " from server " + srv_info['srv'] + \
		#	" 3 times. Stop and exit the streaming!!!")
		#
		#	(srv_info, vchunk_sz) = coop_ft_srv_chunk(srv_info, video_id, vidChunk, v_peers, p_peers)
		#else:
		#	error_num = 0
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
		curBW = num(reps[nextRep]['bw'])
		chunk_QoE = computeQoE(freezingTime, curBW, maxBW)

		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", \
						str(curBuffer), "---|---", str(freezingTime), "---|---", srv_info['srv'], "---|---", str(rsp_time), "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, \
			Freezing=freezingTime, Server=srv_info['srv'], Response=rsp_time)
		srv_qoe_tr[chunkNext] = chunk_QoE

		# Select server for next 12 chunks
		if chunkNext%DASH_PERIOD == 0 and chunkNext > (DASH_PERIOD - 1):
			mnQoE = averageQoE(srv_qoe_tr)
			update_qoe(cache_agent_obj['ip'], srv_info['srv'], mnQoE, alpha)

			#=========================================================================================================
			## Update the average QoE for 6 chunks to the qoe.db
			insert_qoe(video_id, srv_info['srv'], srv_info['ip'], mnQoE)

			#=========================================================================================================
			## Client Cooperation based Adaptive Server Selection
			# srv_info = coop_qoe_srv_selection(mnQoE, srv_info, video_id, p_peers, v_peers)

		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(chunkLen)
		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)

	return