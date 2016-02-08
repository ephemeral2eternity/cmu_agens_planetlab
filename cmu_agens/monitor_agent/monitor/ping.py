'''
PING a server with count times and get the RTT list
'''
from subprocess import Popen, PIPE
import re
import sys

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
    rttList = parsePingRst(stdout, count)
    return rttList

def getMnRTT(ip, count=3):
    rttList = ping(ip, count)
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
        if ("time=" in curline) or ("time<" in curline):
            curDataStr = curline.split(':', 2)[1]
            curDataDict = extractPingInfo(curDataStr)
            # print "curDataDict:", curDataDict
            rtts.append(curDataDict['time'])
    return rtts

def pingVMs(vmList):
    srvRTTs = {}
    srvNames = vmList.keys()
    for srv in srvNames:
        mnRTT = getMnRTT(vmList[srv], 5)
        srvRTTs[srv] = mnRTT
    return srvRTTs

if __name__ == "__main__":
    mnRTT = getMnRTT('rs-cdn.cmu-agens.com')
    print mnRTT
