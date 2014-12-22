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

# get the all the nodes, regardless of current boot state
print "Retrieving node lists ...",
sys.stdout.flush()
all_nodes = plc_api.GetNodes(auth, {}, ['node_id', 'hostname', 'boot_state'])

#for node in all_nodes:
#	print node

have_node_ids = plc_api.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in plc_api.GetNodes(auth, have_node_ids, ['hostname'])]

print "Retrieving nodes that slice ", slice_name, " have!"
for hnode in have_nodes:
	print "Node on slice:", hnode
print "done."

toadd_nodes = []
todel_nodes = []

#toadd_nodes = all_nodes
# nodes is an array of associative arrays/dictionary objects, each one
# corresponding to a node returned. the keys in each array element are
# the keys specified in return_fields
for node_record in all_nodes:
	if (node_record['hostname'] not in have_nodes) and node_record['boot_state'] == 'boot':
		toadd_nodes.append(node_record['hostname'])
	elif (node_record['hostname'] in have_nodes) and node_record['boot_state'] != 'boot':
		todel_nodes.append(node_record['hostname'])
	elif (node_record['hostname'] in have_nodes):
		print node_record['hostname'], node_record['boot_state']

print "Found %d new boot node(s)" % (len(toadd_nodes))
print "Found %d node(s) no longer in boot state" % (len(todel_nodes))

if len(toadd_nodes) > 0:
	# add node to slice
	print "Adding new nodes to slice ...",
	sys.stdout.flush()
	result = plc_api.AddSliceToNodes(auth, slice_name, toadd_nodes)
	if result == 1:
		print "SUCCESS"
	else:
		print "FAILED!"
	sys.stdout.flush()

	fp = open('new-nodes.txt','w')
	for node in toadd_nodes:
		fp.write("%s\n" % (node));
	fp.close()

if len(todel_nodes) > 0:
	#remove nodes from slice
	print "Removing non-boot nodes from slice ...",
	sys.stdout.flush()
	result = plc_api.SliceNodesDel(auth, slice_name, todel_nodes)
	if result == 1:
		print "SUCCESS"
	else:
		print "FALIED!"
	sys.stdout.flush()

print "Writing out all node list ...",
sys.stdout.flush()
	
merged_nodes = sets.Set()

# add in all found nodes
for node in all_nodes:
	merged_nodes.add(node['hostname'].strip())
	
# write out all node list
afp = open('all-nodes.txt','w')
for node in merged_nodes:
        afp.write("%s\n" % (node))
afp.close()
print "done."

# write out current node list
print "Writing out current node list ...",
sys.stdout.flush()

have_node_ids = plc_api.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in plc_api.GetNodes(auth, have_node_ids, ['hostname'])]

cfp = open('current-nodes.txt','w')
for node in have_nodes:
        cfp.write("%s\n" % (node))
cfp.close()
print "done."
