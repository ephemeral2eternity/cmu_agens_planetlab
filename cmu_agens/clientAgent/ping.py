'''
PING a server with count times and get the RTT list
'''
from subprocess import Popen, PIPE
import string
import re
import socket
import time

# server_ip = '104.155.15.0'
PING_PORT = 8717

# Customized Ping Message to a Ping Server using TCP
def ping(ip):
    # Connect to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, PING_PORT))
    # Send a PING message
    message = 'PING'
    ts_sent = time.time()
    len_sent = s.send(message)
    # Receive a response
    response = s.recv(len_sent)
    ts_recv = time.time()
    ## Compute rtt
    rtt = (ts_recv - ts_sent) * 1000
    s.close()
    return rtt

def extract_number(s,notfound='NOT_FOUND'):
    regex=r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    return re.findall(regex,s)

def getRTT(ip, count):
	'''
	Pings a host and return True if it is available, False if not.
	'''
	cmd = ['ping', '-c', str(count), ip]
	process = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	rttList = parsePingRst(stdout, count)
	print rttList

	## Use customized ping server to answer
	#rttList = []
	#for i in range(count):
	#	cur_rtt = ping(ip)
	#	rttList.append(cur_rtt)
	#	time.sleep(0.05)
		
	return rttList

def getMnRTT(ip, count):
	rttList = getRTT(ip, count)
	mnRTT = sum(rttList) / float(len(rttList))
	return mnRTT

def parsePingRst(pingString, count):
	rtts = []
	lines = pingString.splitlines()
	for i in range(1, count+1):
		curline = lines[i]
		# print curline
		curDataStr = curline.split(':', 2)[1]
		curData = extract_number(curDataStr)
		rtts.append(float(curData[-1]))
	return rtts

# if getRTT(server_ip, 5):
#	print '{} is available'.format(server_ip)
#else:
#	print '{} is not available'.format(server_ip)
