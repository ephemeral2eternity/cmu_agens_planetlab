#!/bin/bash

srv="104.197.42.89"
if [ $# -ge 1 ]; then
	srv=$1
fi

rtt=$(ping -c 1 $srv |grep 'time=' |cut -d ':' -f 2|awk '{print $3}' |cut -d '=' -f 2)
echo $HOSTNAME, $rtt
