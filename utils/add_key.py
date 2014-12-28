#!/usr/bin/python
"""
add_key.py

@author Chen Wang
@date 12/2014

Add a new public key to my keys in my slice
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

new_key = sys.argv[3]

## Get PLC_API
plc_api = xmlrpclib.ServerProxy(api_url, allow_none=True)

# get all available keys
print "Available Keys ...",
sys.stdout.flush()
all_keys = plc_api.GetKeys(auth, {}, ['key_type', 'key_id', 'key'])
print all_keys

# get person id
person_name = auth['Username']
person_ids = plc_api.GetPersons(auth, person_name, ['person_id'])
person_id = person_ids[0]['person_id']
print "Person: ", person_name, "; Person ID: ", str(person_id)

# Read new key
print "Read new public key ", new_key, "!"
with open(new_key,'r') as keyFile:
	newKeyStr = keyFile.readlines()
print "Key String: ", newKeyStr[0]

# Add new key
newKey = {}
newKey['key_type'] = 'ssh'
newKey['key'] = newKeyStr[0]
print newKey
add_success = plc_api.AddPersonKey(auth, person_id, newKey)
print "Add Success?", str(add_success)

