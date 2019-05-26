# SophieBot

## Requirements
+ Installed git
+ Installed Python3.6+

## Install pip
    wget https://bootstrap.pypa.io/get-pip.py
    python3 get-pip.py

## Cloning repo
    git clone https://github.com/MrYacha/SophieBot

## Installing requirements
    cd SophieBot
    sudo pip3 install -r requirements.txt

## Installing redis and mongoDB

for Ubuntu:

    sudo apt install redis mongodb

for ArchLinux:

    sudo pacman -S redis
    sudo aur -S mongodb

## Setting config

+ Go to SophieBot/sophie_bot
+ Rename bot_conf.json.example to bot_conf.json
+ Open in text editor
+ Set basic config

## Running

    cd SophieBot
    python3 -m sophie_bot

