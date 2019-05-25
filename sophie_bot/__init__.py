import logging

from pymongo import MongoClient
import redis
import ujson

from telethon import TelegramClient


# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s: %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)


f = open('sophie_bot/bot_conf.json', "r")

SOPHIE_VER = "0.2"
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

bot = TelegramClient('ds', API_ID, API_HASH)

logger.info("----------------------")
logger.info("|    SophieBot {}   |".format(SOPHIE_VER))
logger.info("----------------------")
