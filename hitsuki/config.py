# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2019 pqhaz
#
# This file is part of Hitsuki (Telegram Bot)
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

import os
import sys

import yaml
from envparse import env

from hitsuki.utils.logger import log

DEFAULTS = {
    'LOAD_MODULES': True,
    'DEBUG_MODE': True,

    'REDIS_HOST': 'localhost',
    'REDIS_PORT': 6379,
    'REDIS_DB_FSM': 1,

    'MONGODB_URI': 'localhost',
    'MONGO_DB': 'hitsuki',

    'API_PORT': 8080,

    'JOIN_CONFIRM_DURATION': '30m',
}

CONFIG_PATH = 'data/bot_conf.yaml'
if os.name == 'nt':
    log.debug("Detected Windows, changing config path...")
    CONFIG_PATH = os.getcwd() + "\\data\\bot_conf.yaml"

if os.path.isfile(CONFIG_PATH):
    log.info(CONFIG_PATH)
    for item in (data := yaml.load(open('data/bot_conf.yaml', "r"), Loader=yaml.Loader)):
        DEFAULTS[item.upper()] = data[item]
else:
    log.info("Using env vars")


def get_str_key(name, required=False):
    default = DEFAULTS[name] if name in DEFAULTS else None
    if not (data := env.str(name, default=default)) and not required:
        log.warn('No str key: ' + name)
        return None
    if not data:
        log.critical('No str key: ' + name)
        sys.exit(2)
    else:
        return data


def get_int_key(name, required=False):
    default = DEFAULTS[name] if name in DEFAULTS else None
    if not (data := env.int(name, default=default)) and not required:
        log.warn('No int key: ' + name)
        return None
    if not data:
        log.critical('No int key: ' + name)
        sys.exit(2)
    else:
        return data


def get_list_key(name, required=False):
    default = DEFAULTS[name] if name in DEFAULTS else None
    if not (data := env.list(name, default=default)) and not required:
        log.warn('No list key: ' + name)
        return []
    if not data:
        log.critical('No list key: ' + name)
        sys.exit(2)
    else:
        return data


def get_bool_key(name, required=False):
    default = DEFAULTS[name] if name in DEFAULTS else None
    if not (data := env.bool(name, default=default)) and not required:
        log.warn('No bool key: ' + name)
        return False
    if not data:
        log.critical('No bool key: ' + name)
        sys.exit(2)
    else:
        return data
