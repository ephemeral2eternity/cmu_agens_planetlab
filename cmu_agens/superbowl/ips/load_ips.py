## Read cache server ips from cache_ips

import csv
import os

def load_cache_ips():
    cache_ips = {}
    cache_urls = {}
    cur_folder = os.path.dirname(__file__)
    cache_ip_file = cur_folder + "/cache_ips.csv"

    with open(cache_ip_file, 'r') as cache_file:
        reader = csv.reader(cache_file)
        for row in reader:
            cache_ips[row[0]] = row[1]
            cache_urls[row[0]] = "http://" + row[1] + "/"

    return cache_ips, cache_urls

def load_client_ips():
    client_ips = {}
    cur_folder = os.path.dirname(__file__)
    client_ip_file = cur_folder + "/client_ips.csv"

    with open(client_ip_file, 'r') as cfile:
        reader = csv.reader(cfile)
        for row in reader:
            client_ips[row[0]] = row[1]

    return client_ips

if __name__ == "__main__":
    cache_ips, cache_urls = load_cache_ips()
    print cache_ips, cache_urls

    client_ips = load_client_ips()
    print client_ips
