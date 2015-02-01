# The client agent code
# Client agent is responsible for: downloading the video chunk, play it, monitor QoE and
# switch bitrate, switch server if QoE is not good enough
# @author : chenw@andrew.cmu.edu
import time
import datetime
import shutil
import math
import json
# import requests
import urllib2
import random
from operator import itemgetter
from mpd_parser import *
from download_chunk import *
#from gcs_upload import *

def findRep(sortedVidBWS, est_bw_val, bufferSz, minBufferSz):
	for i in range(len(sortedVidBWS)):
		if sortedVidBWS[i][1] > est_bw_val:
			j = max(i - 1, 0)
			break
		else:
			j = i

	if bufferSz < minBufferSz:
		j = max(j-1, 0)
	elif bufferSz > 20:
		j = min(j + 1, len(sortedVidBWS) - 1)
	
	repID = sortedVidBWS[j][0]
	return repID

def increaseRep(sortedVidBWS, repID):
	dict_sorted_vid_bws = dict(sortedVidBWS)
	i = dict_sorted_vid_bws.keys().index(repID)
	j = min(i+1, len(sortedVidBWS) - 1)
	newRepID = sortedVidBWS[j][0]
	return newRepID

def computeQoE(freezing_time, cur_bw, max_bw):
	delta = 0.5
	a = [1.3554, 40]
	b = [5.0, 6.3484, 4.4, 0.72134]
	q = [5.0, 5.0]

	if freezing_time > 0:
		q[0] = b[0] - b[1] / (1 + math.pow((b[2]/freezing_time), b[3]))

	q[1] = a[0] * math.log(a[1]*cur_bw/max_bw)

	qoe = delta * q[0] + (1 - delta) * q[1]
	return qoe

def num(s):
        try:
                return int(s)
        except ValueError:
                return float(s)

def averageQoE(client_trace, curSrv):
	mn_QoE = 0
	curSrvNum = 0
	if len(client_trace) < 10:
		for chunk_tr in client_trace:
			if client_trace[chunk_tr]["Server"] == curSrv:
				curSrvNum = curSrvNum + 1
				mn_QoE += client_trace[chunk_tr]["QoE"]
		mn_QoE = mn_QoE / curSrvNum
	else:
		for chunk_tr in client_trace.keys()[-10:]:
			if client_trace[chunk_tr]["Server"] == curSrv:
				curSrvNum = curSrvNum + 1
				mn_QoE += client_trace[chunk_tr]["QoE"]
		mn_QoE = mn_QoE / curSrvNum
	return mn_QoE

# ================================================================================
# Query cache agent about how it observes user experiences with all servers
# @input : cache_agent --- The cache agent the user is closest to
# @return: qoe_vector --- QoEs of all servers observed from cache_agent
# ================================================================================
def query_QoE(cache_agent, port):
	req = urllib2.Request("http://" + cache_agent + ":" + str(port) + "/QoE?query")
	res = urllib2.urlopen(req)
	res_headers = res.info()
	# qoe_vector = json.loads(r.headers['Params'])
	qoe_vector = json.loads(res_headers['Params'])
	res.close()
	return qoe_vector

# ================================================================================
# Upload user experiences with a candidate server to cache agent
# @input : cache_agent --- The cache agent the user is closest to
#	   qoe --- User quality experiences with server denoted by server_name over
#		   5 chunks
#	   server_name --- the name of the server the user is downloading chunks from
# @return: qoe_vector --- QoEs of all servers observed from cache_agent
# ================================================================================
# Function has been revised to update_srv_QoEs
#def update_QoE(cache_agent, qoe, server_name):
#	r = requests.get("http://" + cache_agent + "/QoE?update&" + "q=" + str(qoe) + "&s=" + server_name)
#	qoe_vector = json.loads(r.headers['Params'])
#	return qoe_vector

# ================================================================================
# Upload user experiences with all candidate servers to the cache agent
# @input : cache_agent --- The cache agent the user is closest to
#	   qoe --- User quality experiences with server denoted by server_name over
#		   5 chunks
#	   server_name --- the name of the server the user is downloading chunks from
# @return: qoe_vector --- QoEs of all servers observed from cache_agent
# ================================================================================
def update_srv_QoEs(cache_agent, port, server_qoes):
	request_str = "http://" + cache_agent + ":" + str(port) + "/QoE?update"
	for srv in server_qoes.keys():
		request_str = request_str + "&" + srv + "=" + str(server_qoes[srv])
	#r = requests.get(request_str) 
	#qoe_vector = json.loads(r.headers['Params'])
	req = urllib2.Request(request_str)
	res = urllib2.urlopen(req)
	res_headers = res.info()
	qoe_vector = json.loads(res_headers['Params'])
	res.close()
	return qoe_vector

# ================================================================================
# Read candidate server QoE from QoE vectors
# @input : qoe_vector --- QoE Vector obtained from cache agent
#	   server_addrs --- Candidate servers {name:ip} to download a videos
# @return: srv_qoe --- QoEs of candidate servers {srv:qoe}
# ================================================================================
def get_server_QoE(qoe_vector, server_addrs, candidates):
	srv_qoe = {}
	for srv_name in candidates:
		if srv_name not in qoe_vector.keys():
			print "[Client-Agent] Input server name " + srv_name + " does not exist in QoE vector. Check if the cache agent's QoE table is successfully built!!!"
			sys.exit(1)
		if srv_name not in server_addrs.keys():
			print "[Client-Agent] Input server name " + srv_name + " does not exist in server_addrs, please check if the server is still on!!!"
			sys.exit(1)

		srv_qoe[srv_name] = qoe_vector[srv_name]
	return srv_qoe
	
# ================================================================================
# Simple Client to run DASH
# @input : videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
#	   srv_ip --- The ip address of the server
# ================================================================================
def simple_dash(videoName, clientID, srv_ip):
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
                # print "[AGENP] Time Elapsed when downloading :" + str(time_elapsed)
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
                print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|"

                client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, Freezing=freezingTime, Response=rsp_time)

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

        ## Upload the trace file to google cloud
        #bucketName = "agens-data"

# ================================================================================
# Client agent to run DASH
# @input : cache_agent --- Cache agent that is closest to the client
#	   videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
# ================================================================================
def dash(cache_agent, server_addrs, selected_srv, port, videoName, clientID):
	# Initialize server addresses
	srv_ip = server_addrs[selected_srv]

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
		rsp_time = loadTS - curTS
                est_bw = vchunk_sz * 8 / (curTS - loadTS)
                time_elapsed = curTS - preTS
                # print "[AGENP] Time Elapsed when downloading :" + str(time_elapsed)
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
                print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|"

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

        ## Upload the trace file to google cloud
        #bucketName = "agens-data"
        #gcs_upload(bucketName, trFileName)
		
# ================================================================================
# Client agent to run QoE driven Adaptive Server Selection DASH
# @input : cache_agent --- Cache agent that is closest to the client
#	   server_addrs --- Candidate servers {name:ip} to download a videos
#	   videoName --- The name of the video the user is requesting
#	   clientID --- The ID of client.
#	   alpha --- The forgetting factor of local QoE evaluation
# ================================================================================
def qas_dash(cache_agent, server_addrs, candidates, port, videoName, clientID, alpha):
	# Initialize servers' qoe
        cache_agent_ip = server_addrs[cache_agent]
	server_qoes = {}
	for key in candidates:
		if key is cache_agent:
			server_qoes[key] = 5
		else:
			server_qoes[key] = 4

        # Selecting a server with maximum QoE
        selected_srv = max(server_qoes.iteritems(), key=itemgetter(1))[0]
        pre_selected_srv = selected_srv
        selected_srv_ip = server_addrs[selected_srv]

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
        # print "[AGENP] Selected server for next 5 chunks is :" + selected_srv
        # achunk_sz = download_chunk(selected_srv_ip, videoName, audioInit)
        vchunk_sz = download_chunk(selected_srv_ip, videoName, vidInit)
        startTS = time.time()
        print "[QAS-DASH] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
        est_bw = vchunk_sz * 8 / (startTS - loadTS)
        # print "[AGENP] Estimated bandwidth is : " + str(est_bw) + " at chunk #init"
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
		rsp_time = loadTS - curTS
                est_bw = vchunk_sz * 8 / (curTS - loadTS)
                time_elapsed = curTS - preTS
                # print "[AGENP] Time Elapsed when downloading :" + str(time_elapsed)
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

                # Update QoE evaluations on local client
                server_qoes[selected_srv] = server_qoes[selected_srv] * (1 - alpha) + alpha * chunk_QoE
                # print "[AGENP] Current QoE for chunk #" + str(chunkNext) + " is " + str(chunk_QoE)
                print "|---", str(int(curTS)),  "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|"

		# Write out traces
                client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, Freezing=freezingTime, Server=selected_srv, Reponse=rsp_time)
		# Assign values but not dictionary pointer
		new_srv_qoes = {}
		for c in candidates:
			new_srv_qoes[c] = server_qoes[c]
		srv_qoe_tr[chunkNext] = new_srv_qoes
		# srv_qoe_tr[chunkNext] = server_qoes
	
		# Switching servers only after two chunks
		if chunkNext > 4:
			# Selecting a server with maximum QoE
        		pre_selected_srv = selected_srv
			selected_srv = max(server_qoes.iteritems(), key=itemgetter(1))[0]
                	selected_srv_ip = server_addrs[selected_srv]
                	print "[QAS-DASH] Update Server QoEs ar :" + json.dumps(server_qoes)
                	# print "[AGENP] Selected server for next 5 chunks is :" + selected_srv

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

        ## Upload the trace file to google cloud
        #bucketName = "agens-data"
        #gcs_upload(bucketName, trFileName)
	#gcs_upload(bucketName, srv_qoe_tr_filename)

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
                        # nextRep = increaseRep(sortedVids, nextRep)
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
		rsp_time = loadTS - curTS
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

	## Upload the trace file to google cloud
	#bucketName = "agens-data"
	#gcs_upload(bucketName, trFileName)
	#gcs_upload(bucketName, srv_qoe_tr_filename)
