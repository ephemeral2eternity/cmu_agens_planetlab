# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import operator
import urllib2, socket
from ping import *
from client_agent import *

## Get Client Agent Name
def getMyName():
	hostname = socket.gethostname()
	return hostname

video = 'BBB'	
client = getMyName()

cache_server = "cache-05"
cache_server_ip = "104.155.229.210" 

clientID = client + "_simple"

simple_dash(video, clientID, cache_server, cache_server_ip)
