from dash.fault_tolerance import *
from dash.utils import *
from qoe.dash_chunk_qoe import *
from utils.client_utils import *


## ==================================================================================================
# define the simple client agent that only downloads videos from denoted server
# @input : srv_addr ---- the server name address 
#		   video_name --- the string name of the requested video
## ==================================================================================================
def dash_client(srv_addr, video_name, method=None):
	## Define all parameters used in this client
	alpha = 0.5
	retry_num = 10

	## CDN SQS
	CDN_SQS = 5.0
	uniq_srvs = []

	## ==================================================================================================
	## Client name and info
	client = getMyName()
	cur_ts = time.strftime("%m%d%H%M")
	if method is not None:
		client_ID = client + "_" + cur_ts + "_" + method
	else:
		client_ID = client + "_" + cur_ts

	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts, srv_ip = ft_mpd_parser(srv_addr, retry_num, video_name)
	if not rsts:
		return

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
		  " from server : " + srv_addr

	(vchunk_sz, chunk_srv_ip, error_codes) = ft_download_chunk(srv_addr, retry_num, video_name, vidInit)
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
		(vchunk_sz, chunk_srv_ip, error_codes) = ft_download_chunk(srv_addr, retry_num, video_name, vidChunk)
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

		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)
	writeTrace(client_ID + "_httperr", http_errors)
	return client_ID, CDN_SQS, uniq_srvs
