#!/bin/bash
f=$1
N=0
cat $f | while read LINE; do
	N=$((N+1))
	FOLDER="/home/Chen/weekday/log/$LINE/"
	echo "Make directory in $FOLDER"
	if [ ! -d "$FOLDER" ]; then
		mkdir $FOLDER
		echo "${FOLDER} created successfully"
	fi
	echo "Copy Files from $LINE:~/log2100/ to the folder $FOLDER"
	cmd1="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/log2100/*.log $FOLDER"
	echo "run command: $cmd1"
	eval $cmd1
	cmd2="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/log2400/*.log $FOLDER"
	echo "run command: $cmd2"
	eval $cmd2
	cmd3="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/log1030/*.log $FOLDER"
	echo "run command: $cmd3"
	eval $cmd3
	cmd4="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/log0750/*.log $FOLDER"
	echo "run command: $cmd4"
	eval $cmd4
	cmd5="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/log/*.log $FOLDER"
	echo "run command: $cmd5"
	eval $cmd5
done
