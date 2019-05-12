import logging

from pymongo import MongoClient

import redis

from telethon import TelegramClient

import ujson

# logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)

f = open('sophie_bot/bot_conf.json', "r")
conf = ujson.load(f)

OWNER_ID = int(conf["basic"]["owner_id"])

SUDO = list(conf["advanced"]["sudo"])
SUDO.append(OWNER_ID)

WHITELISTED = list(conf["advanced"]["whitelisted"])
WHITELISTED = WHITELISTED + SUDO
#WHITELISTED.append(OWNER_ID)

API_ID = conf["basic"]["app_id"]
API_HASH = conf["basic"]["app_hash"]
TOKEN = conf["basic"]["bot_token"]
MONGO_CONN = conf["basic"]["mongo_conn"]
MONGO_PORT = conf["basic"]["mongo_port"]
NAME = TOKEN.split(':')[0]
BOT_NICK = conf["basic"]["bot_nick"]

bot = TelegramClient(NAME, API_ID, API_HASH)

# Init MongoDB
mongodb = MongoClient(MONGO_CONN).sophie

# Init Redis
redis = redis.StrictRedis(
    host='localhost', port=6379, db='1')  # decode_respone=True
