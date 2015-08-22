## Some utilities for testing script
# Chen Wang, Feb. 18, 2014
# chenw@andrew.cmu.edu
## test_utils.py

import random
import time
import math
import urllib2

## ======================================================================== 
# Wait for a random period of time
# @input : minPeriod ---- The minimum time period to wait
#		   maxPeriod ---- The maximum time period to wait
## ======================================================================== 
def waitRandom(minPeriod, maxPeriod):
	## Sleeping a random interval before starting the client agent
	waitingTime = random.randint(minPeriod, maxPeriod)
	print "Before running DASH on the client agent, sleep %d seconds!" % waitingTime
	time.sleep(waitingTime)

## ======================================================================== 
# Generate the cumulative Distribution Function for Zipf's distribution
# @input : N ---- The number of videos
#		   p ---- The parameter to compute Zipf distribution
# @return : the cumulative distribution function of Zipf
## ======================================================================== 
def getZipfCDF(N, p):
	zipf_cdf = []
	sum_p = 0
	for i in range(N):
		p = math.pow(i + 1, -p)
		sum_p = sum_p + p
		zipf_cdf.append(sum_p)


	zipf_cdf = [x/sum_p for x in zipf_cdf]
	return zipf_cdf

## ======================================================================== 
# Weighted choice a number from zero to the length of dist_cdf
# @input : dist_cdf ---- The cumulative distribution for the weighted choice
# @return : the number choiced from 0 to len(dist_cdf)
## ======================================================================== 
def weighted_choice(dist_pdf):
	rnd = random.random()
	for i, total in enumerate(dist_pdf, start=1):
		if rnd < total:
			return i
