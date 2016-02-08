#!/bin/sh
echo "Installing python-pip!"
cd ~
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python ~/get-pip.py
echo "Display the pip version!"
pip -V
echo "Install python requests packages!"
pip install requests
echo "Upgrading the requests package to the latest version!"
pip install --upgrade requests
