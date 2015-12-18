## Some utilities for DASH streaming
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
import time
import datetime
import math
import json
import random
from operator import itemgetter

# ================================================================================
# Return the integer or float value of a number string
# @input : s --- the string of the number
# ================================================================================
def num(s):
	try:
		return int(s)
	except ValueError:
		return float(s)

## ==================================================================================================
# Find the video bitrate representation ID according to the real-time buffer size and estimated bw
# for DASH streaming
# @input : sortedVidBWS ---- sorted video bitrates dict with repID as the key
#	       est_bw_val ---- estimated real time bandwidth
#          bufferSz ---- real time buffer size
#          minBufferSz ---- the minimum buffer size required according to the mpd file denoted
## ==================================================================================================
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

## ==================================================================================================
# Get the ID of the next larger bitrate representation
# @input : sortedVidBWS ---- sorted video bitrates dict with repID as the key
#	       repID ---- the current representation ID
## ==================================================================================================
def increaseRep(sortedVidBWS, repID):
	dict_sorted_vid_bws = dict(sortedVidBWS)
	i = dict_sorted_vid_bws.keys().index(repID)
	j = min(i+1, len(sortedVidBWS) - 1)
	newRepID = sortedVidBWS[j][0]
	return newRepID