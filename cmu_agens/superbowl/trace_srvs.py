import config
import hosts
from ipinfo.ipinfo import *
from monitor.traceroute import *
from utils import *


startTime = time.time()
time_str = time.strftime('%m%d%H%M')
myName = getMyName()

traceroute_file = config.trace_path + myName + '_' + time_str + '_cache.json'
host_traceroutes = {}

for hname in hosts.cache_ips.keys():
    cur_hostname = hosts.cache_ips[hname]
    cur_ip = host2ip(cur_hostname)
    cur_traceroute = traceroute(cur_ip)
    actual_host_name, host_info = ip2host(cur_ip)
    if not actual_host_name:
        actual_host_name = cur_hostname
    if host_info:
        save_ipinfo(config.info_path, host_info)

    host_traceroutes[hname] = {'hostname':actual_host_name, 'ip':cur_ip, 'routes':cur_traceroute}

writeJson(traceroute_file, host_traceroutes)

time_elapsed = time.time() - startTime
print "Hosts traceroute running time: ", time_elapsed