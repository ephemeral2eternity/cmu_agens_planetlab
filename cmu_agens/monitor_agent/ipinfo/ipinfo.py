import json
import requests
import os
import socket
import struct
from host2ip import *

def is_reserved(ip):
    f = struct.unpack('!I', socket.inet_aton(ip))[0]
    private = (
        [2130706432, 4278190080], # 127.0.0.0,   255.0.0.0   http://tools.ietf.org/html/rfc3330
        [3232235520, 4294901760], # 192.168.0.0, 255.255.0.0 http://tools.ietf.org/html/rfc1918
        [2886729728, 4293918720], # 172.16.0.0,  255.240.0.0 http://tools.ietf.org/html/rfc1918
        [167772160,  4278190080], # 10.0.0.0,    255.0.0.0   http://tools.ietf.org/html/rfc1918
    )
    for net in private:
        if (f & net[1]) == net[0]:
            return True
    return False

def ipinfo(ip):
    url = 'http://ipinfo.io/' + ip
    resp = requests.get(url)
    hop_info = json.loads(resp.text)

    if 'org' in hop_info.keys():
        hop_org = hop_info['org']
        hop_org_items = hop_org.split()
        hop_info['AS'] = hop_org_items[0]
        hop_info['ISP'] = " ".join(hop_org_items[1:])
    return hop_info

def save_ipinfo(outPath, hop_info):
    try:
        os.stat(outPath)
    except:
        os.mkdir(outPath)

    cur_ip = hop_info['ip']
    out_file = outPath + cur_ip + '.json'
    if not os.path.exists(out_file):
        with open(out_file, 'w') as outfile:
            json.dump(hop_info, outfile, sort_keys = True, indent = 4, ensure_ascii=True)


if __name__ == "__main__":
    # hop_name = "et-5-0-0.120.rtr.eqny.net.internet2.edu"
    hop_name = "10.50.20.61"
    if is_hostname(hop_name):
        ip = host2ip(hop_name)
    else:
        ip = hop_name
    print ip

    if is_reserved(ip):
        print ip, " is a private ip!"
    else:
        print ip, " is a public ip!"
        hop_info = ipinfo(ip)
        outPath = 'D://GitHub/monitor_agent/hopData/'
        save_ipinfo(outPath, hop_info)