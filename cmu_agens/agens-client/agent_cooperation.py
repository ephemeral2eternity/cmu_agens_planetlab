# The agent cooperation code
# @author : chenw@andrew.cmu.edu
import urllib2
import json

# ================================================================================
# Query cache agent about how it observes user experiences with all servers
# @input : cache_agent --- The cache agent the user is closest to
# @return: qoe_vector --- QoEs of all servers observed from cache_agent
# ================================================================================
def query_QoE(cache_agent, port):
	req = urllib2.Request("http://" + cache_agent + ":" + str(port) + "/QoE?query")
	res = urllib2.urlopen(req)
	res_headers = res.info()
	qoe_vector = json.loads(res_headers['Params'])
	res.close()
	return qoe_vector

# ================================================================================
# Upload user experiences with one candidate servers to the cache agent
# @input : cache_agent --- The cache agent the user is closest to
#          port ---- the port number the cache agent is running on
#	       qoe --- User quality experiences with server denoted by server_name over
#		   5 chunks
#	       server_name --- the name of the server the user is downloading chunks from
# @return: qoe_vector --- QoEs of all servers observed from cache_agent
# ================================================================================
def update_QoE(cache_agent, port, qoe, srv):
	request_str = "http://" + cache_agent + ":" + str(port) + "/QoE?update"
	request_str = request_str + "&" + srv + "=" + str(qoe)
	req = urllib2.Request(request_str)
	res = urllib2.urlopen(req)
	res_headers = res.info()
	qoe_vector = json.loads(res_headers['Params'])
	res.close()
	return qoe_vector

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