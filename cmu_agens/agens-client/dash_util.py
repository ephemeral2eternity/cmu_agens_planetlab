# The dash representation switching facilities
# @author : chenw@andrew.cmu.edu
def num(s):
        try:
                return int(s)
        except ValueError:
                return float(s)

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