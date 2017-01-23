#!/usr/bin/python
import socket
import time
import re
import sys
from subprocess import Popen, PIPE

def isNum(value):
    try:
        float(value)
        return True
    except ValueError:
        try:
            int(value)
            return True
        except ValueError:
            return False

def is_ip(ip_addr):
    re_ip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    if re_ip.match(ip_addr):
        return True
    else:
        return False

def findAddr(tr_data):
    item_ind = 0
    for item in tr_data:
        if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', item) != None:
            return item_ind, item
        item_ind += 1

    return -1, '*'

def findHostname(tr_data):
    item_ind = 0
    ch_pattern = re.compile('[a-zA-Z]')
    for item in tr_data:
        chars = re.findall(ch_pattern, item)
        if ('.' in item) and (len(chars) > 0):
           return item_ind, item
        item_ind += 1
    return -1, '*'

def traceroute(host):
    hops = dict()
    if sys.platform == 'win32':
        cmd = ['tracert', host]
    else:
        cmd = ['traceroute', '-m', '30', host]
    p = Popen(cmd, stdout=PIPE)
    while True:
        line = p.stdout.readline()
        if not line:
            break

        tr_line = line.replace('ms', '')
        if sys.platform == 'win32':
            ip_addrs = re.findall(r'\[.*?\]', tr_line)
            tr_line = re.sub(r'\[', '', tr_line)
            tr_line = re.sub(r'\]', '', tr_line)

        else:
            ip_addrs = re.findall(r'\(.*?\)', tr_line)
            tr_line = re.sub(r'\(', '', tr_line)
            tr_line = re.sub(r'\)', '', tr_line)

        tr_data = tr_line.split()

        if len(tr_data) < 1:
            continue

        if tr_data[0].isdigit():
            hop_id = int(tr_data[0])
            hop = {}
            addr_ind, addr = findAddr(tr_data)
            hop_name_ind, hop_name = findHostname(tr_data)
            # print hop_name_ind, hop_name

            if hop_name_ind < 0:
                hop['name'] = addr
            else:
                hop['name'] = hop_name
                tr_data.remove(hop_name)

            hop['ip'] = addr
            if addr in tr_data:
                tr_data.remove(addr)
            tr_data.pop(0)

            hop_time_exist = False
            total_hop_time = 0
            probe_times = 0
            for tr_item in tr_data:
                if isNum(tr_item):
                    total_hop_time += float(tr_item)
                    probe_times += 1
                    hop_time_exist = True
                elif '<' in tr_item:
                    total_hop_time += 1
                    probe_times += 1
                    hop_time_exist = True

            if hop_time_exist:
                hop['time'] = total_hop_time / float(probe_times)
            else:
                hop['time'] = '*'
            if len(ip_addrs) > 0:
                hop['ip'] = ip_addrs[0][1:-1]
            elif is_ip(hop['name']):
                hop['ip'] = hop['name']
            else:
                hop['ip'] = '*'
            # print hop
            hops[hop_id] = hop

    return hops

def trVMs(vmList):
    srvHops = {}
    srvNames = vmList.keys()
    for srv in srvNames:
        hops = traceroute(vmList[srv])
        srvHops[srv] = hops
    return srvHops

if __name__ == "__main__":
    hops = traceroute('az.cmu-agens.com')
    # hops = traceroute('plonk.cs.uwaterloo.ca')
    print hops

    hops = traceroute('93.184.221.200')
    print hops
