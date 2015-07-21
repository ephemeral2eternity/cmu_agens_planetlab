#!/usr/bin/python

import socket
import time

def traceroute(dest_name):
    hops = dict()
    dest_addr = socket.gethostbyname(dest_name)
    port = 33434
    max_hops = 30
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 1

    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        recv_socket.bind(("", port))
        recv_socket.settimeout(3)
        ts = time.time()
        send_socket.sendto("", (dest_name, port))
        curr_addr = None
        curr_name = None
        try:
            _, curr_addr = recv_socket.recvfrom(512)
            curr_addr = curr_addr[0]
            try:
                curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
        except socket.error:
            pass
        finally:
            send_socket.close()
            recv_socket.close()
        timeElapsed = (time.time() - ts) * 1000

        if curr_addr is not None:
            curr_host = "%s (%s) %.2f (ms)" % (curr_name, curr_addr, timeElapsed)
            hop_name = str(curr_name)
            hop_addr = str(curr_addr)
        else:
            curr_host = "*"
            hop_name = "*"
            hop_addr = "*"

        print "%d\t%s" % (ttl, curr_host)
        hop = dict()
        hop['Name'] = hop_name
        hop['Addr'] = hop_addr
        hop['Time'] = timeElapsed
        hops[ttl] = hop

        ttl += 1
        if curr_addr == dest_addr or ttl >= max_hops:  
            break

    return hops

if __name__ == "__main__":
    hops = traceroute('104.197.6.6')
    print hops