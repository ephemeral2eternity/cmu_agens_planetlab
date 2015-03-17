#!/usr/bin/python
### get_gce_region.py
### Record which zone and region the client will go to according to the shortest network latency criterion.
import csv
import os
from ping import *

def get_gce_region:
	min_srv_rtt = 2000
	zone = ''
	region = ''

	## Get the current folder of the file
	curpath = os.path.dirname(os.path.realpath(__file__))
	with open(curpath + '/zones.csv', 'rb') as csvfile:
		csvreader = csv.reader(csvfile, delimiter=',')
		for row in csvreader:
			cur_ip = row[0]
			cur_zone = row[1]
			cur_region = row[2]
			cur_rtt = getMnRTT(cur_ip, 5)

			if cur_rtt < min_srv_rtt:
				min_srv_rtt = cur_rtt
				zone = cur_zone
				region = cur_region

	return zone, region
