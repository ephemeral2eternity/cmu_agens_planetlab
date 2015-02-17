'''
PING a server with count times and get the RTT list
'''
from subprocess import Popen, PIPE
import string
import re
import socket
import time
import json

def extract_number(s,notfound='NOT_FOUND'):
    regex=r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    return re.findall(regex,s)

def getRTT(srvname, srv_ip, count, intvl):
	'''
	Pings a host and return True if it is available, False if not.
	'''
	if "az" in srvname:
		cmd = ['sudo', 'tcpping','-C', '-x', str(count), '-r', str(intvl), srv_ip]
	else:
		cmd = ['ping', '-c', str(count), '-i', str(intvl), srv_ip]
	process = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	if "az" in srvname:
		rttList = parseTcppingRst(stdout)
	else:
		rttList = parsePingRst(stdout, count)
	print "Ping List for server ", srvname, " is :", str(rttList)
	return rttList

def getMnRTT(srv_name, srv_ip, count, intvl):
	rttList = getRTT(srv_name, srv_ip, count, intvl)
	if len(rttList) > 0:
		mnRTT = sum(rttList) / float(len(rttList))
	else:
		mnRTT = 500.0
	return mnRTT

def parsePingRst(pingString, count):
	rtts = []
	lines = pingString.splitlines()
	for line in lines:
		curline = line
		# print curline
		if "time=" in curline:
			curDataStr = curline.split(':', 2)[1]
			curData = extract_number(curDataStr)
			rtts.append(float(curData[-1]))
	return rtts

def parseTcppingRst(pingString):
	rtts = []
	rtt_list_str = pingString.split(':', 2)[1]
	rtt_strs = rtt_list_str.split()
	for item in rtt_strs:
		rtts.append(float(item))
	return rtts

def pingAllSrvs(hostname, srvs):
	pingRsts = {}
	for key in srvs:
		cur_rtt = getMnRTT(key, srvs[key], 5, 1)
		pingRsts[key] = cur_rtt

	# print "The RTTs to all available servers are:", str(pingRsts)
	ts = time.time()

	logfile = "./log/" + hostname + "_" + str(int(ts)) + "_PING.json"
	with open(logfile, 'w') as outfile:
		json.dump(pingRsts, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

srvs = {
	'az01' : 'cache-01.cloudapp.net',
	'az02' : 'cache-02.cloudapp.net',
	'az03' : 'cache-03.cloudapp.net',
	'az04' : 'cache-04.cloudapp.net',
	'az05' : 'cache-05.cloudapp.net',
	'az06' : 'cache-06.cloudapp.net',
	'az07' : 'cache-07.cloudapp.net',
	'az08' : 'cache-08.cloudapp.net',
	'az09' : 'cache-09.cloudapp.net',
	'az10' : 'cache-10.cloudapp.net',
	'aws01': '54.152.213.238',
	'aws02': '54.186.168.77',
	'aws03': '54.153.43.107',
	'aws04': '54.77.113.86',
	'aws05': '54.169.179.58',
	'aws06': '54.64.91.44',
	'aws07': '54.153.153.121',
	'aws08': '54.94.144.78',
	'gc01': '107.167.191.63',
	'gc02': '107.167.182.111',
	'gc03': '104.155.211.19',
	'gc04': '104.155.194.20',
	'gc05': '104.155.229.210',
	'gc06': '104.155.225.107',
	'gc07': '130.211.63.102',
	'gc08': '130.211.95.77',
	'gc09': '146.148.115.155',
	'gc10': '104.155.4.67',
	'gc11': '130.211.118.29',
	'gc12': '146.148.89.8',
	'gc13': '130.211.153.45',
	'gc14': '104.154.61.126',
	'gc15': '130.211.115.69',
	'gc16': '104.154.54.212',
	}

curname = socket.gethostname()

N = 2

for n in range(N):
	pingAllSrvs(curname, srvs)
