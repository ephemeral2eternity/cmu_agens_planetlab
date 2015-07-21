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
	cmd = ['ping', '-c', str(count), '-i', '1', ip]
	process = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	rttList = parsePingRst(stdout, count)
	return rttList

def getMnRTT(ip, count):
	rttList = getRTT(ip, count)
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

# if getRTT(server_ip, 5):
#	print '{} is available'.format(server_ip)
#else:
#	print '{} is not available'.format(server_ip)
