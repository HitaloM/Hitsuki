# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import pickle
import sys

from bson.codec_options import TypeDecoder, TypeRegistry
from bson.binary import Binary, USER_DEFINED_SUBTYPE
from motor import motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from sophie_bot import log
from sophie_bot.config import get_str_key, get_int_key

MONGO_URI = get_str_key("MONGO_URI")
MONGO_PORT = get_int_key("MONGO_PORT")
MONGO_DB = get_str_key("MONGO_DB")


def fallback_pickle_encoder(value):
    return Binary(pickle.dumps(value), USER_DEFINED_SUBTYPE)


class PickledBinaryDecoder(TypeDecoder):
    bson_type = Binary

    def transform_bson(self, value, **kwargs):
        if value.subtype == USER_DEFINED_SUBTYPE:
            return pickle.loads(value)
        return value


type_registry = TypeRegistry([PickledBinaryDecoder()], fallback_encoder=fallback_pickle_encoder)
# Init MongoDB
mongodb = MongoClient(MONGO_URI, MONGO_PORT, type_registry=type_registry)[MONGO_DB]
motor = motor_asyncio.AsyncIOMotorClient(MONGO_URI, MONGO_PORT, type_registry=type_registry)
db = motor[MONGO_DB]

try:
    asyncio.get_event_loop().run_until_complete(motor.server_info())
except ServerSelectionTimeoutError:
    sys.exit(log.critical("Can't connect to mongodb! Exiting..."))
