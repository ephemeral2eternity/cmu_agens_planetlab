#!/bin/bash

f=$1
d=$2
t=5
N=0
cat $f | while read LINE; do
	N=$((N+1))
	echo "Copy Files in $d to the $N node: $LINE"
	cmd="timeout $t rsync -avz -e \"ssh -i /home/Chen/.ssh/id_rsa\" $d cmu_agens@$LINE:~/hello/"
	echo "run command: $cmd"
	eval $cmd
done
