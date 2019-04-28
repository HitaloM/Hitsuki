# A simple script to print some messages.
import os
import sys
import time
import logging

from dotenv import load_dotenv
from requests import get
from telethon import TelegramClient
from pymongo import MongoClient
import redis

load_dotenv("bot.config")

# logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def get_env(name, message, cast=str):
    if name in os.environ:
        return os.environ[name]
    while True:
        value = input(message)
        try:
            return cast(value)
        except ValueError as e:
            print(e, file=sys.stderr)
            time.sleep(1)


OWNER_ID = [654839744, 483808054]
WHITELISTED = [] # 518221376

WHITELISTED = WHITELISTED + OWNER_ID

API_ID = os.environ.get("API_ID", None)
API_HASH = os.environ.get("API_HASH", None)
TOKEN = os.environ.get("TOKEN", None)
NAME = TOKEN.split(':')[0]

bot = TelegramClient(NAME, API_ID, API_HASH)

# Init MongoDB
MONGO = MongoClient('localhost', 27017).sophia

# Init Redis
REDIS = redis.StrictRedis(
    host='localhost', port=6379, db='1')  # decode_respone=True
