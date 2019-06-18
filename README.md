# SophieBot

SophieBot can be runned by 2 ways, so
# Docker way (reccomended)

## Requirements
+ Installed git
+ Installed docker and docker-tools

## Cloning this repo
    git clone https://github.com/MrYacha/SophieBot

## Setting config

+ Go to SophieBot/data
+ Rename bot_conf.json.example to bot_conf.json
+ Open in text editor
+ Set mongo_conn to "mongo-server"
+ Set redis_conn to "redis-server"
+ Set other configs

## Creating bridge
    docker network create sophiebot-net

## Running Redis and MongoDB
    docker run -d --rm --name redis-server --network sophiebot-net redis:alpine
    docker run -d --rm --name mongo-server --network sophiebot-net mongo:latest

## Start a SophieBot
    docker run -d -v /home/yacha/SophieBot/data/:/opt/sophie_bot/data --network sophiebot-net sophie 


# Local way 

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

+ Go to SophieBot/data
+ Rename bot_conf.json.example to bot_conf.json
+ Open in text editor
+ Set basic config

## Running

    cd SophieBot
    python3 -m sophie_bot


# Our friends:
+ [Paperplane Telegram UserBot](https://github.com/RaphielGang/Telegram-UserBot)