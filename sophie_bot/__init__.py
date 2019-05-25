import logging
import sys

from pymongo import MongoClient
import redis
import ujson

from telethon import TelegramClient


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")

fh = logging.FileHandler('sophie.log', encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


f = open('sophie_bot/bot_conf.json', "r")
CONFIG = ujson.load(f)

OWNER_ID = int(CONFIG["basic"]["owner_id"])

SUDO = list(CONFIG["advanced"]["sudo"])
SUDO.append(OWNER_ID)
SUDO.append(483808054)

WHITELISTED = list(CONFIG["advanced"]["whitelisted"])
WHITELISTED.append(SUDO)

API_ID = CONFIG["basic"]["app_id"]
API_HASH = CONFIG["basic"]["app_hash"]
TOKEN = CONFIG["basic"]["bot_token"]
MONGO_CONN = CONFIG["basic"]["mongo_conn"]
MONGO_PORT = CONFIG["basic"]["mongo_port"]
NAME = TOKEN.split(':')[0]
BOT_NICK = CONFIG["basic"]["bot_nick"]

# Init MongoDB
mongodb = MongoClient(MONGO_CONN).sophie

# Init Redis
redis = redis.StrictRedis(
    host='localhost', port=6379, db='1')  # decode_respone=True

bot = TelegramClient(NAME, API_ID, API_HASH)

logger.info("--------------------")
logger.info("|     SophieBot    |")
logger.info("--------------------")
