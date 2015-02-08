# The dash QoE monitoring tools
# @author : chenw@andrew.cmu.edu
import math

def computeQoE(freezing_time, cur_bw, max_bw):
	delta = 0.2
	a = [1.3554, 40]
	b = [5.0, 6.3484, 4.4, 0.72134]
	q = [5.0, 5.0]

	if freezing_time > 0:
		q[0] = b[0] - b[1] / (1 + math.pow((b[2]/freezing_time), b[3]))

	q[1] = a[0] * math.log(a[1]*cur_bw/max_bw)

	qoe = delta * q[0] + (1 - delta) * q[1]
	return qoe


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
