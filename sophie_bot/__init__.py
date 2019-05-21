import logging

from pymongo import MongoClient

import redis

from teleredis import RedisSession

from telethon import TelegramClient

import ujson

# logger = logging.getLogger(__name__)


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

fh = logging.FileHandler('sophie.log', mode='w', encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


f = open('sophie_bot/bot_conf.json', "r")
conf = ujson.load(f)

OWNER_ID = int(conf["basic"]["owner_id"])

SUDO = list(conf["advanced"]["sudo"])
SUDO.append(OWNER_ID)

WHITELISTED = list(conf["advanced"]["whitelisted"])
WHITELISTED = WHITELISTED + SUDO

API_ID = conf["basic"]["app_id"]
API_HASH = conf["basic"]["app_hash"]
TOKEN = conf["basic"]["bot_token"]
MONGO_CONN = conf["basic"]["mongo_conn"]
MONGO_PORT = conf["basic"]["mongo_port"]
NAME = TOKEN.split(':')[0]
BOT_NICK = conf["basic"]["bot_nick"]

# Init MongoDB
mongodb = MongoClient(MONGO_CONN).sophie

# Init Redis
redis = redis.StrictRedis(
    host='localhost', port=6379, db='1')  # decode_respone=True

session = RedisSession(NAME, redis)

bot = TelegramClient(session, API_ID, API_HASH)
