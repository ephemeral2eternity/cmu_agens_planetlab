# The client agent code
# Client agent is responsible for: downloading the video chunk, play it, monitor QoE and
# switch bitrate, switch server if QoE is not good enough
# @author : chenw@andrew.cmu.edu
import time
import datetime
import shutil
import math
import json
import urllib2
import random
import httplib
from operator import itemgetter
from dash_util import *
from dash_qoe import *
from agent_cooperation import *
from mpd_parser import *
from download_chunk import *
from keepalive_download_chunk import *

# ================================================================================
# Client agent to run collaborative QoE driven Adaptive Server Selection DASH
# @input : cache_agent --- Cache agent that is closest to the client
#	   server_addrs --- Candidate servers {name:ip} to download a videos
#	   videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
# ================================================================================
def cqas_dash(cache_agent, server_addrs, candidates, port, videoName, clientID, alpha):
	# Initialize servers' qoe
	cache_agent_ip = server_addrs[cache_agent]
	qoe_vector = query_QoE(cache_agent_ip, port)
	server_qoes = get_server_QoE(qoe_vector, server_addrs, candidates)

	# Selecting a server with maximum QoE
	selected_srv = max(server_qoes.iteritems(), key=itemgetter(1))[0]
	pre_selected_srv = selected_srv
	selected_srv_ip = server_addrs[selected_srv]

	rsts = mpd_parser(selected_srv_ip, videoName)
	vidLength = int(rsts['mediaDuration'])
	minBuffer = num(rsts['minBufferTime'])
	reps = rsts['representations']

	vidBWs = {}
    good_chunks = {}

    for c in candidates:
        good_chunks[c] = 0

	for rep in reps:
		if not 'audio' in rep:
			vidBWs[rep] = int(reps[rep]['bw'])		
		else:
			audioID = rep
			audioInit = reps[rep]['initialization']
			start = reps[rep]['start']
			audioName = reps[rep]['name']

	sortedVids = sorted(vidBWs.items(), key=itemgetter(1))

	minID = sortedVids[0][0]
	vidInit = reps[minID]['initialization']
	maxBW = sortedVids[-1][1]

	# Read common parameters for all chunks
	timescale = int(reps[minID]['timescale'])
	chunkLen = int(reps[minID]['length']) / timescale
	chunkNext = int(reps[minID]['start'])

	# Start downloading video and audio chunks
	curBuffer = 0
	chunk_download = 0
	loadTS = time.time()
	print "[CQAS-DASH] Start downloading video " + videoName + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
	print "[CQAS-DASH] Selected server for next 5 chunks is :" + selected_srv
	vchunk_sz = download_chunk(selected_srv_ip, videoName, vidInit)
	startTS = time.time()
	print "[CQAS-DASH] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
	est_bw = vchunk_sz * 8 / (startTS - loadTS)
	print "|-- TS --|-- Chunk # --|- Representation -|-- QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|"
	preTS = startTS
	chunk_download += 1
	curBuffer += chunkLen

	## Traces to write out
	client_tr = {}
	srv_qoe_tr = {}

	while (chunkNext * chunkLen < vidLength) :
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)

		# Greedily increase the bitrate because server is switched to a better one
		if (pre_selected_srv != selected_srv):
                        prob = good_chunks[selected_srv] / float(vidLength/chunkLen)
                        rnd = random.random()
                        ## Probabilistic switching
                        if rnd < prob:
                                print "[CQAS-DASH] Stick with the previous server! The probability is : " + str(prob)
                                selected_srv = pre_selected_srv
                        else:
                             print "[CQAS-DASH]Switch server! The probability is : " + str(prob)
			     nextRep = increaseRep(sortedVids, nextRep)

		vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkNext))
		loadTS = time.time();
		vchunk_sz = download_chunk(selected_srv_ip, videoName, vidChunk)
		curTS = time.time()
		rsp_time = curTS - loadTS
		est_bw = vchunk_sz * 8 / (curTS - loadTS)
		time_elapsed = curTS - preTS
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
		# print "[AGENP] Current QoE for chunk #" + str(chunkNext) + " is " + str(chunk_QoE)
                # Update QoE evaluations on local client
                server_qoes[selected_srv] = server_qoes[selected_srv] * (1 - alpha) + alpha * chunk_QoE
		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, Freezing=freezingTime, Server=selected_srv, Response=rsp_time)
		srv_qoe_tr[chunkNext] = server_qoes

                if chunk_QoE > 4.0:
                        good_chunks[selected_srv] = good_chunks[selected_srv] + 1

		# Count Previous QoE average
		if chunkNext%10 == 0 and chunkNext > 4:
			# mnQoE = averageQoE(client_tr, selected_srv)
			## qoe_vector = update_QoE(cache_agent_ip, mnQoE, selected_srv)
			qoe_vector = update_srv_QoEs(cache_agent_ip, port, server_qoes)
			server_qoes = get_server_QoE(qoe_vector, server_addrs, candidates)
			print "[CQAS-DASH] Received Server QoE is :" + json.dumps(server_qoes)
			print "[CQAS-DASH] Selected server for next 10 chunks is :" + selected_srv

		# Selecting a server with maximum QoE
		if chunkNext > 4:
			# Selecting a server with maximum QoE
        		pre_selected_srv = selected_srv
			selected_srv = max(server_qoes.iteritems(), key=itemgetter(1))[0]
                	selected_srv_ip = server_addrs[selected_srv]
                	print "[CQAS-DASH] Update Server QoEs ar :" + json.dumps(server_qoes)
                	# print "[AGENP] Selected server for next 10 chunks is :" + selected_srv

		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(chunkLen)
		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	# trFileName = "./data/" + clientID + "_" + videoName + "_" + str(time.time()) + ".json"
	## Writer out traces files and upload to google cloud
	trFileName = "./data/" + clientID + "_" + videoName + ".json"
	with open(trFileName, 'w') as outfile:
		json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)
	srv_qoe_tr_filename = "./data/" + clientID + "_" + videoName + "_srvqoe.json"
	with open(srv_qoe_tr_filename, 'w') as outfile:
		json.dump(srv_qoe_tr, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
	
	shutil.rmtree('./tmp')
