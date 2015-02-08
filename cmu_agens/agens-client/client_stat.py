## Get the statistics from a client trace file
import numpy

## Get statistics from trace file
def get_qoe_stat(client_trace):
	qoes = []
	for key in client_trace:
		chunk_info = client_trace[key]
		qoes.append(chunk_info['QoE'])
	qoe_stat = {}
	qoe_stat['Average'] = sum(qoes)/float(len(qoes))
	qoe_stat['Std'] = numpy.std(qoes)
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
		cur_stat['Average'] = sum(rsp_times[key])/float(len(rsp_times[key]))
		cur_stat['Std'] = numpy.std(rsp_times[key])
		rsp_stat[key] = cur_stat
	return rsp_stat
