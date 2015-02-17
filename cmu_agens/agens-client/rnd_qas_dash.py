# The QoE Adaptive Server Selection Integrated DASH Client
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
from operator import itemgetter
from dash_util import *
from dash_qoe import *
from agent_cooperation import *
from mpd_parser import *
from download_chunk import *
from keepalive_download_chunk import *
		
# ================================================================================
# Client agent to run QoE driven Adaptive Server Selection DASH
# @input : cache_agent --- Cache agent that is closest to the client
#	   server_addrs --- Candidate servers {name:ip} to download a videos
#	   videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
#	   alpha --- The forgetting factor of local QoE evaluation
# ================================================================================
def rnd_qas_dash(candidates, videoName, clientID, alpha):
	# Initialize servers' qoe
	server_qoes = {}
	for key in candidates:
		server_qoes[key] = 4

        # Selecting a server randomly
        selected_srv = random.choice(candidates.keys())
        pre_selected_srv = selected_srv
        selected_srv_ip = candidates[selected_srv]

        rsts = mpd_parser(selected_srv_ip, videoName)
        vidLength = int(rsts['mediaDuration'])
        minBuffer = num(rsts['minBufferTime'])
        reps = rsts['representations']

        vidBWs = {}
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
        print "[AGENP] Start downloading video " + videoName + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
        vchunk_sz = download_chunk(selected_srv_ip, videoName, vidInit)
        startTS = time.time()
        print "[QAS-DASH] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
        est_bw = vchunk_sz * 8 / (startTS - loadTS)
        print "|-- TS --|-- Chunk # --|- Representation -|-- QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|"
        preTS = startTS
        chunk_download += 1
        curBuffer += chunkLen

	# Traces to write out.
        client_tr = {}
	srv_qoe_tr = {}

        while (chunkNext * chunkLen < vidLength) :
		# Compute the representation for the next chunk to be downloaded                
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)

		# Greedily increase the bitrate because server is switched to a better one
		if (pre_selected_srv != selected_srv):
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
                else:
                        freezingTime = 0
                        curBuffer = curBuffer - time_elapsed

                # Compute QoE of a chunk here
                curBW = num(reps[nextRep]['bw'])
                chunk_QoE = computeQoE(freezingTime, curBW, maxBW)

                # Update QoE evaluations on local client
                server_qoes[selected_srv] = server_qoes[selected_srv] * (1 - alpha) + alpha * chunk_QoE
                print "|---", str(int(curTS)),  "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|"

		# Write out traces
                client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, Freezing=freezingTime, Server=selected_srv, Reponse=rsp_time)
		# Assign values but not dictionary pointer
		new_srv_qoes = {}
		for c in candidates:
			new_srv_qoes[c] = server_qoes[c]
		srv_qoe_tr[chunkNext] = new_srv_qoes
	
		# Switching servers only after two chunks
		if chunkNext > 4:
			# Selecting a server with maximum QoE
        		pre_selected_srv = selected_srv
			selected_srv = max(server_qoes.iteritems(), key=itemgetter(1))[0]
                	selected_srv_ip = server_addrs[selected_srv]
                	print "[QAS-DASH] Update Server QoEs ar :" + json.dumps(server_qoes)

                # Update iteration information
                curBuffer = curBuffer + chunkLen
                if curBuffer > 30:
                        time.sleep(chunkLen)
                preTS = curTS
                chunk_download += 1
                chunkNext += 1

	## Write trace files out and upload to google cloud storage
        trFileName = "./data/" + clientID + "_" + videoName + ".json"
        with open(trFileName, 'w') as outfile:
                json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

	srv_qoe_tr_filename = "./data/" + clientID + "_" + videoName + "_srvqoe.json"
	with open(srv_qoe_tr_filename, 'w') as outfile:
		json.dump(srv_qoe_tr, outfile, sort_keys=True, indent=4, ensure_ascii=False)

        shutil.rmtree('./tmp')