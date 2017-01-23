#!/usr/bin/python
"""
rm_nodes.py

@author Chen Wang
@date 12/2014
Remove current nodes from current slice
"""

import sys
import xmlrpclib
import sets

# PlanetLab PLCAPI url
plc_host='www.planet-lab.org'
api_url="https://%s:443/PLCAPI/"%plc_host

# in Python, this creates a dictionary, or associative array.
auth= {}
auth['Username']= sys.argv[1]
# always 'password', for password based authentication
auth['AuthMethod']= "password"
auth['AuthString']= sys.argv[2]
# valid roles include, 'user', 'tech', 'pi', 'admin'
auth['Role']= "user"
slice_name = 'cmu_agens'

# Nodes file to delete
nodes_todel_file = sys.argv[3]

## Get PLC_API
plc_api = xmlrpclib.ServerProxy(api_url, allow_none=True)

# get the all the nodes, regardless of current boot state
print "Retrieving nodes on slice ", slice_name
have_node_ids = plc_api.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in plc_api.GetNodes(auth, have_node_ids, ['hostname'])]

todel_nodes = []

with open(nodes_todel_file) as fd:
	lines = fd.readlines()
	for ln in lines:
		node_name = ln.rstrip('\n')
		if node_name in have_nodes:
			todel_nodes.append(node_name)
			print "Delete node: " + node_name

print "Found %d node(s) to be deleted" % (len(todel_nodes))

if len(todel_nodes) > 0:
	#remove nodes from slice
	print "Removing nodes from slice ..."
	sys.stdout.flush()
	result = plc_api.SliceNodesDel(auth, slice_name, todel_nodes)
	if result == 1:
		print "SUCCESS"
	else:
		print "FALIED!"
	sys.stdout.flush()

print "done."
