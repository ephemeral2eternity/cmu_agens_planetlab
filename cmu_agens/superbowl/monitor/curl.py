'''
Curl a URL to get the response time for downloading the page
'''
from subprocess import Popen, PIPE
import re
import sys
import os

## Call system command to ping a
def curl(url):
    '''
    Curl a url and record the response time.
    '''
    cmd = ['curl', '-o', '/dev/null', '-s', '-w', '%{time_connect}:%{time_starttransfer}:%{time_total}', url]
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    # print stdout

    return stdout


if __name__ == "__main__":
    url = "http://www.cbssports.com/nfl/superbowl/live/player"
    rsp_times = curl(url)
    print rsp_times