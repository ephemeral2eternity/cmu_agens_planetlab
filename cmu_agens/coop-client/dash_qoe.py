# The dash QoE monitoring tools
# @author : chenw@andrew.cmu.edu
import math
import urllib2

## ==================================================================================================
# Compute per chunk QoE based on the video bitrate, the maximum available bitrate and freezing caused
# by current chunk
# @input : freezing_time --- the freezing time caused by current chunk
#		   cur_bw ---- the bitrate of current chunk
#		   max_bw ---- the maximum bitrate available
## ==================================================================================================
def computeQoE(freezing_time, cur_bw, max_bw):
	delta = 0.2            # The minimum bitrate corresponds to QoE=1 if there is no freezing.
	a = [1.3554, 40]
	b = [5.0, 6.3484, 4.4, 0.72134]
	q = [5.0, 5.0]

	if freezing_time > 0:
		q[0] = b[0] - b[1] / (1 + math.pow((b[2]/freezing_time), b[3]))

	q[1] = a[0] * math.log(a[1]*cur_bw/max_bw)

	qoe = delta * q[0] + (1 - delta) * q[1]
	return qoe

## ==================================================================================================
# Get the average of previous 12 chunk QoEs (1 minute) on a given server
# @input : srv_qoe_tr --- the per chunk qoe dictionary with the key as the chunk ID
## ==================================================================================================
def averageQoE(srv_qoe_tr):
	mn_QoE = 0.0
	curSrvNum = 0
	if len(srv_qoe_tr) < 6:
		for chunk_id in srv_qoe_tr.keys():
			curSrvNum = curSrvNum + 1
			mn_QoE += srv_qoe_tr[chunk_id]
		
	else:
		## Study chunks in the previous 1 minute
		chunk_ids = sorted(srv_qoe_tr.keys())
		last_minute_chunk_ids = chunk_ids[-6:]
		print "Average QoE for chunk ids: ", str(last_minute_chunk_ids)
		for chunk_id in last_minute_chunk_ids:
			curSrvNum = curSrvNum + 1
			mn_QoE += srv_qoe_tr[chunk_id]
	mn_QoE = mn_QoE / float(curSrvNum)
	return mn_QoE

## ==================================================================================================
# Update the selected server experience to the cache agent
# @input : cache_agent_ip --- the ip address of the cache agent the user attached to
#		   selected_srv --- the name of the selected server for streaming in previous 1 minute
#		   minuteQoE --- the average chunk QoE in previous 1 minute
#		   alpha --- the weight given to the updated QoE
## ==================================================================================================
def update_qoe(cache_agent_ip, selected_srv, minuteQoE, alpha):
	url = "http://%s:8615/qoe/update?srv=%s&qoe=%.4f&alpha=%.2f" % (cache_agent_ip, selected_srv, minuteQoE, alpha)
	# print url
	try:
		rsp = urllib2.urlopen(url)
		print "Update QoE for server :", selected_srv, " to cache agent ", cache_agent_ip, " successfully!"
	except:
		print "Failed to update QoE for server ", selected_srv, " to cache agent ", cache_agent_ip
		pass


