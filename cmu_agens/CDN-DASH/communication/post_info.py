import urllib2
import json
import os
from monitor.get_device_info import *
from monitor.get_hop_info import *


############################################################################
# Report the route information for the client to the cloud agent
# Cloud agent: locator
# Client info: client_info
# Whether it is QWatch or QDiag system: isDiag = True represents QDiag System
#############################################################################
def report_route(locator, client_info, isDiag=True):
    ## Debug URL
    if isDiag:
        url = "http://%s/diag/add" % locator
    else:
        url = "http://%s/locator/add" % locator
    # url = "http://%s/diag/add" % locator

    isSuccess = True
    try:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(client_info))
    except:
        isSuccess = False

    return isSuccess

def checkRouteCached(locator, client_ip, srv_ip):
    url = "http://%s/locator/exist?client=%s&server=%s" % (locator, client_ip, srv_ip)

    isRouteCached = True
    try:
        response = urllib2.urlopen(url)
        client_info = json.load(response)
        if client_info['ip'] == client_ip:
            isRouteCached = True
        else:
            isRouteCached = False
    except:
        isRouteCached = False

    return isRouteCached

def updateRoute(locator, client_ip, srv_ip, qoe):
    url = "http://%s/locator/update?client=%s&server=%s&qoe=%f" % (locator, client_ip, srv_ip, qoe)

    isRouteUpdated = True
    try:
        response = urllib2.urlopen(url)
        response_str = response.read()
        if response_str == "Yes":
            isRouteUpdated = True
        else:
            isRouteUpdated = False
    except:
        isRouteUpdated = False
        print "Failed to update route info to %s" % locator

    return isRouteUpdated


def updateAttribute(diagAgent, client_ip, srv_ip, qoe):
    url = "http://%s/diag/update?client=%s&server=%s&qoe=%f" % (diagAgent, client_ip, srv_ip, qoe)

    isUpdated = True
    try:
        response = urllib2.urlopen(url)
        response_str = response.read()
        if response_str == "Yes":
            isUpdated = True
        else:
            isUpdated = False
    except:
        isRouteUpdated = False
        print "Failed to update good QoE to %s" % diagAgent

    return isUpdated


def cache_client_info(locator, client_info, srv_ip, cdn_host, isDiag=True):
    client_ip = client_info['ip']
    # isRouteCached = checkRouteCached(locator, client_ip, srv_ip)

    # if not isRouteCached:
    cdnHops = get_hop_by_host(srv_ip)
    srv_info = get_node_info(srv_ip)

    client_info['server'] = srv_info
    if cdnHops[-1]['ip'] != srv_info['ip']:
        cdnHops.append(srv_info)
    cdnHops[-1]['name'] = cdn_host

    client_info['route'] = cdnHops

    outJsonFileName = os.getcwd() + "/routeData/" + client_info['name'] + "-" + client_info['server']['name'] + ".json"
    with open(outJsonFileName, 'wb') as f:
        json.dump(client_info, f)

    # route_str = route2str(cdnHops)
    # print route_str
    isSuccess = False
    tries = 0
    while (tries < 3) and (not isSuccess):
        isSuccess = report_route(locator, client_info, isDiag)
        tries += 1

    if isSuccess:
        print "Successfully report route from client ", client_ip, " to server ", srv_ip, " to the anomaly locator " \
                , "agent ", locator
    else:
        print "Failed to report route to anomaly locator agent:", locator

    # else:
    #    print "Route from client ", client_ip, " to server ", srv_ip, " is cached in the anomaly locator!"


def add_event(diagAgent, client, eventType, prevVal, curVal):
    url = "http://%s/diag/addEvent?client=%s&typ=%s&prev=%s&cur=%s" % (diagAgent, client, eventType, prevVal, curVal)

    try:
        response = urllib2.urlopen(url)
        response_str = response.read()
        if response_str == "Yes":
            isAdded = True
        else:
            isAdded = False
    except:
        isAdded = False

    return isAdded


def locate_anomaly(locator, client_ip, srv_ip, qoe):
    url = "http://%s/locator/locate?client=%s&server=%s&qoe=%.3f" % (locator, client_ip, srv_ip, qoe)

    anomaly_info = {}
    try:
        response = urllib2.urlopen(url)
        response_str = response.read()
        anomaly_info = json.loads(response_str)
        print "Located anomaly info:", anomaly_info
    except:
        print "Failed to locate the anomaly for streaming session from client ", client_ip, " to server ", srv_ip
    return anomaly_info

def diagnose_anomaly(diagAgent, client_ip, srv_ip, qoe, anomalyType):
    # url = "http://%s/locator/locate?client=%s&server=%s&qoe=%.3f" % (locator, client_ip, srv_ip, qoe)
    url = "http://%s/diag/diag?client=%s&server=%s&qoe=%.3f&type=%s" % (diagAgent, client_ip, srv_ip, qoe, anomalyType)

    anomaly_info = {}
    try:
        response = urllib2.urlopen(url)
        response_str = response.read()
        anomaly_info = json.loads(response_str)
        print "Diagnosed anomaly info:", anomaly_info
    except:
        print "Failed to diagnose the anomaly for streaming session from client ", client_ip, " to server ", srv_ip
    return anomaly_info

def route2str(full_route):
    route_list = []
    for node in full_route:
        route_list.append(node['ip'])

    route_str = ','.join(str(e) for e in route_list)
    return route_str

if __name__ == '__main__':
    server_ip = "93.184.221.200"
    cdn_host = "az.cmu-agens.com"
    diagAgent = "40.117.35.106"
    client_ip, client_info = get_ext_ip()
    client = client_info["name"]
    client_info["device"] = get_device_info()
    cache_client_info(diagAgent, client_info, server_ip, cdn_host)
    qoe = 3.5
    # anomaly_info = locate_anomaly(locator, client_ip, server_ip, qoe)
    isUpdated = updateAttribute(diagAgent, client_ip, server_ip, qoe)
    # print isUpdated

    eventType = "server_switch"
    preVal = server_ip
    server_ip = "72.21.81.200"
    curVal = server_ip

    cache_client_info(diagAgent, client_info, server_ip, cdn_host)
    isAdded = add_event(diagAgent, client_ip, eventType, preVal, curVal)
    print isAdded

    anomalyType = "occasional"
    qoe = 1.2
    diagResult = diagnose_anomaly(diagAgent, client_ip, server_ip, qoe, anomalyType)

    #isUpdated = updateRoute(locator, client_ip, srv2_ip, qoe)
    #print isUpdated
    # qoe = 0.5
    # client_ip = "128.237.191.151"
    # anomaly_info = locate_anomaly(locator, client_ip, server_ip, qoe)
    # anomaly_info = locate_anomaly(locator, client_ip, srv2_ip, qoe)