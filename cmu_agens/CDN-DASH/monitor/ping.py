'''
PING a server with count times and get the RTT list
'''
from subprocess import Popen, PIPE
import re
import sys
import time

def extract_number(s):
    regex=r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    return re.findall(regex,s)

def extractPingInfo(pingStr):
    curDataList = pingStr.split()
    pingData = {}
    for curData in curDataList:
        # print curData
        if '=' in curData:
            dataStr = curData.split('=')
            dataVal = extract_number(dataStr[1])
            pingData[dataStr[0]] = float(dataVal[0])
        elif '<' in curData:
            dataStr = curData.split('<')
            dataVal = extract_number(dataStr[1])
            pingData[dataStr[0]] = float(dataVal[0])
    return pingData

## Call system command to ping a
def ping(ip, count):
    '''
    Pings a host and return True if it is available, False if not.
    '''
    if sys.platform == 'win32':
        cmd = ['ping', '-n', str(count), ip]
    else:
        cmd = ['ping', '-c', str(count), ip]
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print stdout
    rttList, srv_ip = parsePingRst(stdout, count)
    return rttList, srv_ip

def getMnRTT(ip, count=3):
    rttList, srv_ip = ping(ip, count)
    if len(rttList) > 0:
        mnRTT = sum(rttList) / float(len(rttList))
    else:
        mnRTT = 500.0
    return mnRTT, srv_ip

def parsePingRst(pingString, count):
    rtts = []
    srv_ip = None
    lines = pingString.splitlines()
    for line in lines:
        curline = line
        # print curline
        if ("time=" in curline) or ("time<" in curline):
            curDataStr = curline.split(':', 2)[1]
            curDataDict = extractPingInfo(curDataStr)
            # print "curDataDict:", curDataDict
            rtts.append(curDataDict['time'])

        if not srv_ip:
            tmp = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', curline)
            if tmp:
                srv_ip = tmp.group()
    return rtts, srv_ip

def pingVMs(vmList):
    srvRTTs = {}
    srvNames = vmList.keys()
    for srv in srvNames:
        mnRTT = getMnRTT(vmList[srv], 5)
        srvRTTs[srv] = mnRTT
    return srvRTTs


if __name__ == "__main__":
    time_start = time.time()
    mnRTT, srv_ip = getMnRTT('az.cmu-agens.com')
    duration = time.time() -  time_start
    print srv_ip, mnRTT, duration
