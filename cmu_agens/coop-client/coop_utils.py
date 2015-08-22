## Some utilities for cooperative agents
# Chen Wang, Jun. 17, 2015
# chenw@andrew.cmu.edu
## coop_utils.py
import random
import time
import datetime
import math
import os
import urllib2
import sqlite3 as lite
from calendar import timegm
from attach_cache_agent import *
from traceroute import *
from sys_traceroute import *

# Note: if you pass in a naive dttm object it's assumed to already be in UTC
def unix_time(dttm=None):
    if dttm is None:
       dttm = datetime.utcnow()

    return timegm(dttm.utctimetuple())

## ======================================================================== 
# Create and Initialize a database to keep
## ========================================================================
def create_db():
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	# Create or connect to the denoted database
	con = lite.connect(db_name)
	cur = con.cursor()

	# Check if there exists a table called QoE.
	cur.execute("DROP TABLE IF EXISTS QoE;")
	cur.execute("CREATE TABLE QoE(vidID int, srvName text, srvIP text, QoE real, TS datetime);")
	cur.execute("INSERT INTO QoE(vidID, srvName, srvIP, QoE, TS) values (?, ?, ?, ?, ?)", (1, 'cache-01', '104.197.42.89', 5.0, datetime.datetime.now()))
	cur.execute("INSERT INTO QoE(vidID, srvName, srvIP, QoE, TS) values (?, ?, ?, ?, ?)", (1, 'cache-02', '104.197.59.54', 5.0, datetime.datetime.now()))
	cur.execute("INSERT INTO QoE(vidID, srvName, srvIP, QoE, TS) values (?, ?, ?, ?, ?)", (1, 'cache-03', '104.197.8.50', 5.0, datetime.datetime.now()))

	con.commit()	
	con.close()

#==========================================================================================
# Get Traceroutes to all available servers
#==========================================================================================
def get_all_routes():
	## Try several times before exit
	all_cache_agents = get_cache_agents()
	trial_num = 0
	while not all_cache_agents and trial_num < 10:
		all_cache_agents = get_cache_agents()
		trial_num = trial_num + 1

	all_srv_hops = dict()
	for srv in all_cache_agents.keys():
		# srv_hops = traceroute(all_cache_agents[srv])
		srv_hops = sys_traceroute(all_cache_agents[srv])
		all_srv_hops[all_cache_agents[srv]] = srv_hops

	return all_srv_hops

#==========================================================================================
# Read the client's latest QoE and streaming server address for a certain video
#==========================================================================================
def get_info(vidID):
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	con = lite.connect(db_name)
	cur = con.cursor()

	SELECT_CMD = "SELECT * FROM QoE WHERE vidID=%d ORDER BY TS DESC LIMIT 1" % vidID
	cur.execute(SELECT_CMD)
	lite_info = cur.fetchall()
	con.close()

	## Read the server name, server address and the video ID.
	if len(lite_info) > 0:
		srv = lite_info[0][2]
		video = lite_info[0][0]
		qoe = lite_info[0][3]
		srv_name = lite_info[0][1]
		ts = lite_info[0][4]

		info = dict()
		info['srv'] = srv
		info['srvName'] = srv_name
		info['qoe'] = float(qoe)
		info['video'] = video
		info['ts'] = unix_time(ts)

	## Should add code to handle empty info.
	else:
		info = {}

	return info

#==========================================================================================
# Read the client's latest QoE and streaming server address from qoe.db
#==========================================================================================
def get_latest():
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	con = lite.connect(db_name)
	cur = con.cursor()

	SELECT_CMD = "SELECT * FROM QoE ORDER BY TS DESC LIMIT 1"
	cur.execute(SELECT_CMD)
	lite_info = cur.fetchall()
	con.close()

	## Read the server name, server address and the video ID.
	if len(lite_info) > 0:
		## Read the server name, server address and the video ID.
		srv = lite_info[0][2]
		video = lite_info[0][0]
		qoe = lite_info[0][3]
		srv_name = lite_info[0][1]
		ts = lite_info[0][4]

		info = dict()
		info['srv'] = srv
		info['srvName'] = srv_name
		info['qoe'] = float(qoe)
		info['video'] = video
		info['ts'] = unix_time(ts)

	else:
		info = {}

	return info

#==========================================================================================
# Update INFO to qoe.db
#==========================================================================================
def insert_qoe(video_id, srv_name, srv_ip, qoe):
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	## Connect to the local qoe.db
	con = lite.connect(db_name)
	cur = con.cursor()

	## Update the average QoE for 6 chunks to the qoe.db
	cur.execute("INSERT INTO QoE(vidID, srvName, srvIP, QoE, TS) values (?, ?, ?, ?, ?)", (video_id, srv_name, srv_ip, qoe, datetime.datetime.now()))
	con.commit()
	con.close()

#==========================================================================================
# Insert Route info to qoe.db
#==========================================================================================
def insert_route(all_routes):
	full_path = os.path.realpath(__file__)
	path, fn = os.path.split(full_path)
	db_name = path + "/qoe.db"

	## Connect to the local qoe.db
	con = lite.connect(db_name)
	cur = con.cursor()

	# Check if there exists a table called Route.
	cur.execute("DROP TABLE IF EXISTS Route;")
	cur.execute("CREATE TABLE Route(srvIP text, srvRoute text);")

	## Insert all the routes from current client to all servers into qoe.db
	for srv in all_routes.keys():
		cur_route = get_route_str(srv, all_routes)
		cur.execute("INSERT INTO Route(srvIP, srvRoute) values (?, ?)", (srv, cur_route))

	con.commit()
	con.close()

#==========================================================================================
# Get the string of route info from all routes
# @input: srv ---- the server the client is streaming from
#         all_routes ---- all traceroute info from client to the streaming server, srv
# @return : the string of all hops in the route from the client to the streaming server
#==========================================================================================
def get_route_str(srv, all_routes):
	cur_route = all_routes[srv]

	cur_route_list = []
	for hop_id in cur_route.keys():
		cur_route_list.append(cur_route[hop_id]['Name'])

	cur_route_str = ', '.join(cur_route_list)
	return cur_route_str
