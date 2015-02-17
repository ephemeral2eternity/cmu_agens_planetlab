# The random dash client code
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

# ================================================================================
# Client agent to run Random DASH
# @input : candidates --- Candidate servers that the client can chooose one (It's 
#                       the dict data with server name as keys)
#	   videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
# ================================================================================
def rnd_dash(candidates, videoName, clientID):
	# Initialize the selection of server
        selected_srv = random.choice(candidates.keys())
	srv_ip = candidates[selected_srv]

	# Read MPD file
	rsts = mpd_parser(srv_ip, videoName)
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
        print "[DASH] Start downloading video " + videoName + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
        vchunk_sz = download_chunk(srv_ip, videoName, vidInit)
        startTS = time.time()
        print "[DASH] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
        est_bw = vchunk_sz * 8 / (startTS - loadTS)
        print "|-- TS -- |-- Chunk # --|- Representation -|-- QoE --|-- Buffer --|-- Freezing --|-- Server --|"
        preTS = startTS
        chunk_download += 1
        curBuffer += chunkLen
	
	# Traces to write to google cloud
        client_tr = {}

        while (chunkNext * chunkLen < vidLength) :
                nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)
                vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkNext))
                loadTS = time.time();
                vchunk_sz = download_chunk(srv_ip, videoName, vidChunk)
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
                print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|---", str(rsp_time), "---|"

                client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, Freezing=freezingTime, Server=selected_srv, Response=rsp_time)

                # Update iteration information
                curBuffer = curBuffer + chunkLen
                if curBuffer > 30:
                        time.sleep(chunkLen)
                preTS = curTS
                chunk_download += 1
                chunkNext += 1

        trFileName = "./data/" + clientID + "_" + videoName + ".json"
	with open(trFileName, 'w') as outfile:
                json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

        shutil.rmtree('./tmp')

        return client_tr