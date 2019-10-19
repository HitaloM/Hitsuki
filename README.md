
# Sophie Telegram Bot

>  Sophie is modern and fast Telegram chat manager bot

    
## Requirements  
  
+ Install git, python 3.8+ and docker(for docker method) from your package manager  
+ You need to know how to clone this repo  
  
  
## Docker Way  
  
### Cloning this repo  
	 git clone https://github.com/MrYacha/SophieBot  
### Setting config  
  
+ Go to SophieBot/data  
+ Rename bot_conf.yaml.example to bot_conf.yaml  
+ Open in text editor  
+ Set mongo_conn to "mongo-server"  
+ Set redis_conn to "redis-server"  
+ Set other configs as needed  
  
### Creating bridge  
	 docker network create sophiebot-net  
### Running Redis and MongoDB  
	 docker run -d --rm --name redis-server --network sophiebot-net redis:alpine docker run -d --rm --name mongo-server --network sophiebot-net mongo:latest  
### Start a SophieBot  
	 docker run -d -v /home/yacha/SophieBot/data/:/opt/sophie_bot/data --network sophiebot-net sophie   
  
## Manual way 
  
  
### Cloning this repo  
	 git clone https://github.com/MrYacha/SophieBot  
  
### Setting config  
  
+ Go to SophieBot/data  
+ Rename bot_conf.json.example to bot_conf.json  
+ Open in text editor  
+ Set configs as needed  
  
### Installing requirements  
	 cd SophieBot
	 sudo pip3.8 install -r requirements.txt
	 sudo apt install redis mongodb (from your package manager)
  
### Running  
  
	 cd SophieBot
	 python3.8 -m sophie_bot
