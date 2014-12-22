#!/usr/bin/python
"""
download_logs.py

@author Brian Sanderson
@date 1/2007

Downloads boot nodes into slice and generates node lists.
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

## Get PLC_API
plc_api = xmlrpclib.ServerProxy(api_url, allow_none=True)

## All nodes added to the slice
have_node_ids = plc_api.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in plc_api.GetNodes(auth, have_node_ids, ['hostname'])]

print "Retrieving nodes that slice ", slice_name, " have!"
for hnode in have_nodes:
	print hnode
print "done."

print "Writing out all node list ...",
sys.stdout.flush()
	
cfp = open('current-nodes.txt','w')
for node in have_nodes:
        cfp.write("%s\n" % (node))
cfp.close()
print "done."
