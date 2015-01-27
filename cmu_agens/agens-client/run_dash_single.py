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

cache_server_ip = "130.211.118.29" 

clientID = client + "_SINGLE_DASH"

simple_dash(video, clientID, cache_server_ip)
