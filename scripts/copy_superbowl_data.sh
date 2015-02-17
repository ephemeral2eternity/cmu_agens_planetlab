#!/bin/bash
f=$1
N=0
cat $f | while read LINE; do
	N=$((N+1))
	FOLDER="/home/Chen/weekday/data/$LINE/"
	echo "Make directory in $FOLDER"
	if [ ! -d "$FOLDER" ]; then
		mkdir $FOLDER
		echo "${FOLDER} created successfully"
	fi
	echo "Copy Files from $LINE:~/data/ to the folder $FOLDER"
	cmd1="scp -i /home/Chen/.ssh/id_rsa -r cmu_agens@$LINE:~/data/* $FOLDER"
	echo "run command: $cmd1"
	eval $cmd1
	# cmd2="gsutil cp -r gs://super-bowl/data2100/$LINE* $FOLDER"
	# echo "run command: $cmd2"
	# eval $cmd2
	# cmd3="gsutil cp -r gs://super-bowl/data2400/$LINE* $FOLDER"
	# echo "run command: $cmd3"
	# eval $cmd3
done
