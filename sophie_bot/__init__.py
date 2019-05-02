import logging
import ujson

from telethon import TelegramClient
from pymongo import MongoClient
import redis

# logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)

f = open('sophie_bot/bot_conf.json', "r")
conf = ujson.load(f)

OWNER_ID = int(conf["basic"]["owner_id"])
WHITELISTED = list(conf["advanced"]["whitelisted"])
WHITELISTED.append(OWNER_ID)

API_ID = conf["basic"]["app_id"]
API_HASH = conf["basic"]["app_hash"]
TOKEN = conf["basic"]["bot_token"]
NAME = TOKEN.split(':')[0]

bot = TelegramClient(NAME, API_ID, API_HASH)

# Init MongoDB
mongodb = MongoClient('localhost', 27017).sophia

# Init redis
redis = redis.StrictRedis(
    host='localhost', port=6379, db='1')  # decode_respone=True
