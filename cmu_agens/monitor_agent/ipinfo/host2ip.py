import re
import socket

def is_hostname(hop_name):
    ch_pattern = re.compile('[a-zA-Z]')
    chars = re.findall(ch_pattern, hop_name)
    if len(chars) > 0:
        return True
    else:
        return False

def host2ip(hop_name):
    ip = socket.gethostbyname(hop_name)
    return ip

if __name__ == "__main__":
    hop_name = "et-5-0-0.120.rtr.eqny.net.internet2.edu"
    if is_hostname(hop_name):
        ip = host2ip(hop_name)
    else:
        ip = hop_name

    print ip