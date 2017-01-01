import urllib2
import json


############################################################################
# Report the route information to the centralized manager
# Centralized manager: manage.cmu-agens.com
# Client info: client_info
#############################################################################
def report_route_to_manager(manager, client_info):
    ## Debug URL
    url = "http://%s/nodeinfo/add" % manager
    isSuccess = True
    try:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(client_info))
        print(response)
    except:
        isSuccess = False

    return isSuccess


############################################################################
# Report the video session to the centralized manager
# Centralized manager: manage.cmu-agens.com
# Client info: client_info
#############################################################################
def report_video_session(manager, client_info):
    ## Debug URL
    url = "http://%s/verify/add_video_session" % manager
    isSuccess = True
    try:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(client_info))
        print(response)
    except:
        isSuccess = False

    return isSuccess

############################################################################
# Report the verification session to the centralized manager
# Centralized manager: manage.cmu-agens.com
# Client info: client_info
#############################################################################
def report_verify_session(manager, client_info):
    ## Debug URL
    url = "http://%s/verify/add_verify_session" % manager
    isSuccess = True
    try:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(client_info))
        print(response)
    except:
        isSuccess = False

    return isSuccess

############################################################################
# Get the clients, cache servers, and cloud agents in the sytem
# Centralized manager: manage.cmu-agens.com
# @return allNodes
#############################################################################
def get_all_nodes(manager):
    url = "http://%s/getJsonData" % manager
    try:
        rsp = urllib2.urlopen(url)
        allNodes = json.load(rsp)
        return allNodes
    except:
        return {}

############################################################################
# Get the verify agents that cover the networks from current source
# manager: manage.cmu-agens.com
# @return: the list of destination verify agents
############################################################################
def get_verify_agents(manager):
    url = "http://%s/verify/get_verify_session_by_src" % manager
    try:
        rsp = urllib2.urlopen(url)
        verify_agents_info = json.load(rsp)
        return verify_agents_info
    except:
        return {}