import urllib2
from monitor.ping import *

def addRTT(monitor, src, dst, results):
    rtt, srv_ip = getMnRTT(dst)

    if not srv_ip:
        srv_ip = dst

    # url = "http://%s/rtt/add?src=%s&dst=%s&rtt=%.4f" % (monitor, src, dst, rtt)

    curTS = time.time()
    cur_rst = dict(TS=curTS, src=src, dst=srv_ip, rtt=rtt)
    results.put(cur_rst)

    #try:
    #    rsp = urllib2.urlopen(url)
    #    print "Probing %s successfully" % dst
    #except:
    #    print "Failed to probe %s" % dst


def addQoE(monitor, src, dst, chunkID, qoe):
    url = "http://%s/qoe/add?src=%s&dst=%s&id=%d&qoe=%.4f" % (monitor, src, dst, chunkID, qoe)
    try:
        rsp = urllib2.urlopen(url)
        print "Add QoE successfully"
    except:
        print "Failed to report QoE to %s" % monitor