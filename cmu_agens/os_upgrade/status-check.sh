#!/bin/sh
echo "###############################################"
echo "Name:$(hostname)"
echo "OS: $(cat /etc/redhat-release)"
echo -n "Python Version:"
python -c 'import sys; print sys.version_info[:]'
echo -n "Python-requests:"
python -c 'import pkgutil; print(1 if pkgutil.find_loader("requests") else 0)'
echo "Giti version: $(git version)"
echo "Crond status: $(service crond status)"
echo "manage.cmu-agens.com: $(ping -c 1 manage.cmu-agens.com | grep -ohE "\(([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\)" | head -1 | sed "s/[()]//g")"
