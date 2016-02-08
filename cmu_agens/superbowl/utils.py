import json
import socket
import csv
import urllib2
from ipinfo.ipinfo import *

# ================================================================================
## Get Client Agent External IP Address
# ================================================================================
def get_ext_ip():
	try:
		response = urllib2.urlopen("http://curlmyip.com")
	except:
		try:
			response = urllib2.urlopen("http://myexternalip.com/raw")
		except:
			return ""

	ext_ip_line = response.read()
	ext_ip = ext_ip_line.rstrip()
	return ext_ip

# ================================================================================
## Get Client Agent Hostname
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	not_found_names = {
		"221.199.217.144" : "planetlab1.research.nicta.com.au",
		"221.199.217.145" : "planetlab2.research.nicta.com.au"
	}

	if '.' not in hostname:
		ext_ip = get_ext_ip()
		myInfo = ipinfo(ext_ip)
		if "hostname" in myInfo.keys():
			if '.' in myInfo["hostname"]:
				hostname = myInfo["hostname"]
		elif ext_ip in not_found_names.keys():
			hostname = not_found_names[ext_ip]

		if '.' not in hostname:
			hostname = ext_ip
	return hostname



## ==================================================================================================
# Writing json files
# @input : client_ID --- the client ID to write traces
# 		   client_tr --- the client trace dictionary
## ==================================================================================================
def writeJson(file_name, json_var):
	with open(file_name, 'w') as outfile:
		json.dump(json_var, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

## ==================================================================================================
# Append data to a csv file as a new row
# @input : client_ID --- the client ID to write traces
# 		   client_tr --- the client trace dictionary
## ==================================================================================================
def appendCSV(file_name, headers, row_data):
	if not os.path.exists(file_name):
		with open(file_name, 'a+') as rtt_csv:
			writer = csv.DictWriter(rtt_csv, fieldnames=headers, delimiter=',')
			writer.writeheader()
			writer.writerow(row_data)
	else:
		with open(file_name, 'a+') as rtt_csv:
			writer = csv.DictWriter(rtt_csv, fieldnames=headers, delimiter=',')
			writer.writerow(row_data)
	return