import re
import socket

def is_hostname(hop_name):
    ch_pattern = re.compile('[a-zA-Z]')
    # print hop_name
    chars = re.findall(ch_pattern, hop_name)
    if len(chars) > 0:
        return True
    else:
        return False

def is_ip(ip_addr):
    re_ip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    if re_ip.match(ip_addr):
        return True
    else:
        return False

def host2ip(hop_name):
    try:
        ip = socket.gethostbyname(hop_name)
    except socket.error:
        # print "[Error]The hostname : ", hop_name, " can not be resolved!"
        ip = "*"
    return ip

if __name__ == "__main__":
    hop_name = "et-5-0-0.120.rtr.eqny.net.internet2.edu"
    if is_hostname(hop_name):
        ip = host2ip(hop_name)
    else:
        ip = hop_name

    # print ip