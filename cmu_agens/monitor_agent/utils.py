import json
import os
import socket

# ================================================================================
## Get Client Agent Name
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	return hostname

## ==================================================================================================
# Write JSON file to the dataQoE folder
# @input : json_file_name --- json file name
# 		   json_var --- json variable
## ==================================================================================================
def writeJson(json_file_name, json_var):
	trFolder = os.getcwd() + "/data/"
	# Create a cache folder locally
	try:
		os.stat(trFolder)
	except:
		os.mkdir(trFolder)

	if json_var:
		trFileName = trFolder + json_file_name + ".json"
		with open(trFileName, 'w') as outfile:
			json.dump(json_var, outfile, sort_keys = True, indent = 4, ensure_ascii=True)
