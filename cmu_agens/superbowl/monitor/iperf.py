'''
Curl a URL to get the response time for downloading the page
'''
from subprocess import Popen, PIPE
import re
import sys
import os

## Call system command to ping a
def iperf(ip):
    '''
    Curl a url and record the response time.
    '''
    bw_data_list = []

    os.system("killall -9 iperf")

    cmd = ['iperf', '-c', ip, '-d', '-t1', '-y', 'C']
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    for row in process.stdout:
        bw_data = {}
        print row
        if ',' in row:
            items = row.split(',')
            if len(items) == 9:
                bw_data['Timestamp'] = items[0]
                bw_data['Client'] = items[1]
                bw_data['CPort'] = items[2]
                bw_data['Server'] = items[3]
                bw_data['SPort'] = items[4]
                bw_data['ID'] = items[5]
                bw_data['Period'] = items[6]
                bw_data['BytesTransfered'] = int(items[7])
                bw_data['Bandwidth'] = int(items[8])
                bw_data_list.append(bw_data)

    return bw_data_list


if __name__ == "__main__":
    host = "104.196.21.142"
    bw_data_list = iperf(host)
    for bw_data in bw_data_list:
        print bw_data