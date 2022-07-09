#!/bin/bash

apt-get update -y
apt-get install -y python3 python3-pip unzip curl fuse
curl https://rclone.org/install.sh | bash
pip3 install git+https://github.com/heston/Pyrebase.git@a77bd6f6def656b1dcd77d938fac2707f3c4ba61#egg
