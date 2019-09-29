# SophieBot

SophieBot can be ran in 2 ways.

Using Docker is always recommended, as its setup is automated, and needs a very little knowledge of Linux or Command Line.
You also gain an advantage of isolating your server from the Sophie Bot.

You need to configure this bot a bit before it can be used, don't worry, its easy!


# Warning
If you see "SyntaxError: invalid syntax" error - install python3.8+!


# Requirements

+ Install git, python 3.8+ and docker(for docker method) from your package manager
+ You need to know how to clone this repo


# Docker Way

## Cloning this repo
    git clone https://github.com/MrYacha/SophieBot

## Setting config

+ Go to SophieBot/data
+ Rename bot_conf.json.example to bot_conf.json
+ Open in text editor
+ Set mongo_conn to "mongo-server"
+ Set redis_conn to "redis-server"
+ Set other configs as needed

## Creating bridge
    docker network create sophiebot-net

## Running Redis and MongoDB
    docker run -d --rm --name redis-server --network sophiebot-net redis:alpine
    docker run -d --rm --name mongo-server --network sophiebot-net mongo:latest

## Start a SophieBot
    docker run -d -v /home/yacha/SophieBot/data/:/opt/sophie_bot/data --network sophiebot-net sophie 


# I am an old man, I like to go the manual way...


## Cloning this repo
    git clone https://github.com/MrYacha/SophieBot


## Setting config

+ Go to SophieBot/data
+ Rename bot_conf.json.example to bot_conf.json
+ Open in text editor
+ Set configs as needed

## Installing requirements
    cd SophieBot
    sudo pip3 install -r requirements.txt
   
    redis and mongodb from your package manager

## Running

    cd SophieBot
    python3 -m sophie_bot
