#!/bin/sh

echo "Installing necessary packages python!"
cp -r /home/cmu_agens/os_update/fedora* /etc/yum.repos.d/
yum -y upgrade
yum -y install python-requests
