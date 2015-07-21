#!/usr/bin/python

import socket
import time
import re
from subprocess import Popen, PIPE

def sys_traceroute(host):
    hops = dict()
    p = Popen(['traceroute', '-q', '1', host], stdout=PIPE)
    while True:
        line = p.stdout.readline()
        if not line:
            break

        tr_line = line.replace('ms', '')
        tr_data = tr_line.split()

        if tr_data[0].isdigit():
            hop_id = int(tr_data[0])
            hop = {}
            if len(tr_data) < 4:
                hop['Addr'] = "*"
                hop['Name'] = "*"
                hop['Time'] = "*"
            else:
                Addr = tr_data[2].replace('(', '')
                Addr = Addr.replace(')', '')
                hop['Addr'] = Addr
                hop['Name'] = tr_data[1]
                hop['Time'] = float(tr_data[3])
            # print hop
            hops[hop_id] = hop

    return hops

if __name__ == "__main__":
    hops = sys_traceroute('104.197.6.6')
    print hops