#!/bin/bash

#安装必要依赖
apt-get update -y
apt-get install -y python3 python3-pip unzip curl fuse tar
curl https://raw.githubusercontent.com/popliz/IConvert-action/main/rclone_install.sh | bash
pip3 install chardet git+https://github.com/heston/Pyrebase.git@a77bd6f6def656b1dcd77d938fac2707f3c4ba61#egg

#安装字体
cp -r ./fonts/ttf/. /usr/local/share/fonts/truetype
cp -r ./fonts/otf/. /usr/local/share/fonts/opentype
cp ./fonts/fonts.conf /etc/fonts/fonts.conf
chmod 644 -R /usr/local/share/fonts/truetype /usr/local/share/fonts/opentype /etc/fonts/fonts.conf
fc-cache

#安装ffmpeg
curl -LOJ https://github.com/lizkes/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-nonfree.tar.xz
tar -xvf ffmpeg-master-latest-linux64-nonfree.tar.xz
rm ffmpeg-master-latest-linux64-nonfree.tar.xz
mkdir -p /usr/local/bin
mv ./ffmpeg-master-latest-linux64-nonfree/bin/ffmpeg ./ffmpeg-master-latest-linux64-nonfree/bin/ffprobe /usr/local/bin
rm -rf ./ffmpeg-master-latest-linux64-nonfree
