## Do a PING/CURL/iperf Test to denoted commercial hosts or urls
# test_cdn_client.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import config

import hosts
import time
from datetime import datetime
from utils import *
from monitor.ping import *
from monitor.curl import *
from monitor.iperf import *

probe_num = 1

rtt_data = {}
curl_data = {}
bw_data_list = []

myName = getMyName()

curTS = time.time()
dateStr = datetime.fromtimestamp(curTS).strftime('%m%d')

rtt_data['Timestamp'] = curTS
curl_data['Timestamp'] = curTS

for url_name in hosts.cache_urls.keys():
    rsp_time = curl(hosts.cache_urls[url_name])
    curl_data[url_name] = rsp_time

for host_name in hosts.cache_ips.keys():
    mnRTT = getMnRTT(hosts.cache_ips[host_name], probe_num)
    rtt_data[host_name] = mnRTT

rtt_file_name = config.probe_path + myName + '_' + dateStr + '_cacheping.csv'
rtt_headers = ['Timestamp'] + hosts.cache_ips.keys()
appendCSV(rtt_file_name, rtt_headers, rtt_data)


curl_file_name = config.probe_path + myName + '_' + dateStr +'_cachecurl.csv'
curl_headers = ['Timestamp'] + hosts.cache_urls.keys()
appendCSV(curl_file_name, curl_headers, curl_data)

now = datetime.now()
cur_min = now.minute

if cur_min % 5 == 0:
    for host_name in hosts.cache_ips.keys():
        cur_bw_data_list = iperf(hosts.cache_ips[host_name])
        bw_data_list = bw_data_list + cur_bw_data_list

    iperf_file_name = config.probe_path + myName + '_' + dateStr +'_cachebw.csv'
    bw_headers = bw_data_list[0].keys()
    for bw_data in bw_data_list:
        appendCSV(iperf_file_name, bw_headers, bw_data)

time_elapsed = time.time() - curTS
print "Running Time at ", str(curTS), ' is ', str(time_elapsed)




