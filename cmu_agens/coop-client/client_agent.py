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
from mpd_parser import *
from download_chunk import *
from client_utils import *
from failover import *

## ==================================================================================================
# define client_agent method that streams a video using server-side controlled server selection
# @input : cache_agent_obj --- the dict denoting cache agent ip and name
#		   video_id --- the video id the client is requesting
#		   method --- selecting server according to which method
#					  Available methods are: load, rtt, hop, random, qoe
## ==================================================================================================
def client_agent(cache_agent_obj, video_id, method, expID=None):
	## Read info from cache_agent_obj
	cache_agent_ip = cache_agent_obj['ip']
	cache_agent = cache_agent_obj['name']

	## ==================================================================================================
	## Client name and info
	## ==================================================================================================
	client = str(socket.gethostname())
	if expID:
		client_ID = client + "_" + expID + "_" + method
	else:
		cur_ts = time.strftime("%m%d%H%M")
		client_ID = client + "_" + cur_ts + "_" + method
	videoName = 'st'

	## ==================================================================================================
	## Get the initial streaming server
	## ==================================================================================================
	srv_info = get_srv(cache_agent_ip, video_id, method)


	## ==================================================================================================
	## Cache agent failure handler
	## ==================================================================================================
	if not srv_info:
		srv_info = srv_failover(client_ID, video_id, method, cache_agent_ip)

	## If the failover has taken action but still not get the srv_info, it says the cache agent is done.
	if (not srv_info) and (method is 'qoe'):
		logging.info("[" + client_ID + "]Agens client fails to get the server for video " + str(video_id) + " 10 times. Trying to reconnect to a new cache agent!!!")
		# Attache to a new cache agent.
		cache_agent_obj = attach_cache_agent()
		if cache_agent_obj:
			cache_agent_ip = cache_agent_obj['ip']
			cache_agent = cache_agent_obj['name']
			srv_info = srv_failover(client_ID, video_id, method, cache_agent_ip)

	## If the srv_info is stil not got yet
	if not srv_info:
		reportErrorQoE(client_ID, cache_agent_obj['name'])
		return
	## ==================================================================================================

	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts = mpd_parser(srv_info['ip'], videoName)

	### ===========================================================================================================
	## Add mpd_parser failure handler
	### ===========================================================================================================
	if not rsts:
		logging.info("[" + client_ID + "]Agens client can not download mpd file for video " + videoName + " from server " + srv_info['srv'] + \
					"Stop and exit the streaming for methods other than QoE. For qoe methods, get new srv_info!!!")

		if method == "qoe":
			trial_time = 0
			while (not rsts) and (trial_time < 10):
				update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
				srv_info = srv_failover(client_ID, video_id, method, cache_agent_ip)
				if srv_info:
					rsts = mpd_parser(srv_info['ip'], videoName)
				else:
					rsts = ''
					# Attache to a new cache agent.
					cache_agent_obj = attach_cache_agent()
					if cache_agent_obj:
						cache_agent_ip = cache_agent_obj['ip']
						cache_agent = cache_agent_obj['name']
				trial_time = trial_time + 1

			if not rsts:
				reportErrorQoE(client_ID, srv_info['srv'])
				return
		else:
			update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
			reportErrorQoE(client_ID, srv_info['srv'])
			return
	
	### ===========================================================================================================
	### Connecting to the qoe.db
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	con = lite.connect(db_name)
	cur = con.cursor()


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
		while (vchunk_sz == 0) and (error_num < 10):
			# Try to download again the chunk
			vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
			error_num = error_num + 1

		### ===========================================================================================================
		## Failover control for the timeout of chunk request
		### ===========================================================================================================
		if vchunk_sz == 0:
			logging.info("[" + client_ID + "]Agens client can not download chunks video " + videoName + " from server " + srv_info['srv'] + \
			" 3 times. Stop and exit the streaming!!!")

			## Retry to download the chunk
			if method == "qoe":
				trial_time = 0
				while (vchunk_sz == 0) and (trial_time < 10):
					update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
					logging.info("[" + client_ID + "]Agens client failed to download chunk from " + srv_info['srv'] + ". Update bad QoE and rechoose server from cache agent " + cache_agent + "!!!")
					srv_info = srv_failover(client_ID, video_id, method, cache_agent_ip)
					if srv_info:
						logging.info("[" + client_ID + "]Agens choose a new server " + srv_info['srv'] + " for video " + str(video_id) + " from cache agent " + cache_agent + "!!!")
						vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
					else:
						vchunk_sz = 0
						# Attache to a new cache agent.
						cache_agent_obj = attach_cache_agent()
						if cache_agent_obj:
							cache_agent_ip = cache_agent_obj['ip']
							cache_agent = cache_agent_obj['name']
							logging.info("[" + client_ID + "]Agens client can not contact cache agent and reconnects to cache agent " + cache_agent + "!!")
					trial_time = trial_time + 1
				if vchunk_sz == 0:
					reportErrorQoE(client_ID, srv_info['srv'], trace=client_tr)
					return
			## Write out 0 QoE traces for clients.
			else:
				update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
				reportErrorQoE(client_ID, srv_info['srv'], trace=client_tr)
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
		curBW = num(reps[nextRep]['bw'])
		chunk_QoE = computeQoE(freezingTime, curBW, maxBW)

		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", \
						str(curBuffer), "---|---", str(freezingTime), "---|---", srv_info['srv'], "---|---", str(rsp_time), "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, \
			Freezing=freezingTime, Server=srv_info['srv'], Response=rsp_time)
		srv_qoe_tr[chunkNext] = chunk_QoE

		# Select server for next 12 chunks
		if chunkNext%6 == 0 and chunkNext > 3:
			mnQoE = averageQoE(srv_qoe_tr)
			update_qoe(cache_agent_ip, srv_info['srv'], mnQoE, alpha)

			#=========================================================================================================
			## Update the average QoE for 6 chunks to the qoe.db
			cur.execute("INSERT INTO QoE(vidID, srvName, srvIP, QoE, TS) values (?, ?, ?, ?, ?)", (video_id, srv_info['srv'], srv_info['ip'], mnQoE, datetime.datetime.now()))
			con.commit()
			#=========================================================================================================

			if method == "qoe":
				new_srv_info = get_srv(cache_agent_ip, video_id, method)
				if 'ip' in new_srv_info.keys():
					print "[" + client_ID + "] Selected server for next 6 chunks is :" + srv_info['srv']
					srv_info = new_srv_info
				else:
					logging.info("[" + client_ID + "]Agens client failed to choose server for video " + str(video_id) + " from cache agent " + cache_agent + "!!!")

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

	## Close the connection to database.
	con.close()

	return