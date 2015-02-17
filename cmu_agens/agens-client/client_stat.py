## Get the statistics from a client trace file

def get_mn(data):
	mn = sum(data) / float(len(data))
	return mn

def get_std(data):
	mn = get_mn(data)
	ss = sum((x - mn)**2 for x in data)
	pvar = ss / float(len(data))
	std = pvar**0.5
	return std

## Get statistics from trace file
def get_qoe_stat(client_trace):
	qoes = []
	for key in client_trace:
		chunk_info = client_trace[key]
		qoes.append(chunk_info['QoE'])
	qoe_stat = {}
	qoe_stat['Average'] = get_mn(qoes)
	qoe_stat['Std'] = get_std(qoes)
	return qoe_stat

## Get statistics from trace file
def get_rsp_stat(client_trace):
	rsp_times = {}
	for key in client_trace:
		chunk_info = client_trace[key]
		srv = chunk_info['Server']
		if srv not in rsp_times.keys():
			rsp_times[srv] = []
		rsp_times[srv].append(chunk_info['Response'])
	rsp_stat = {}
	for key in rsp_times:
		cur_stat = {}
		cur_stat['Average'] = get_mn(rsp_times[key])
		cur_stat['Std'] = get_std(rsp_times[key])
		rsp_stat[key] = cur_stat
	return rsp_stat
