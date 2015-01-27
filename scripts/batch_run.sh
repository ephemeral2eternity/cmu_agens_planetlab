#!/bin/bash

f=$1
c=$2
t=30
N=0
cat $f | while read LINE; do
	N=$((N+1))
	echo "Run command \"$c\" on the $N node: $LINE"
	echo "run command: $c"
	ssh -i /home/Chen/.ssh/id_rsa -l cmu_agens -t $LINE "$c"
	echo "wait 5 minutes to finish!!"
	sleep 5m
done
