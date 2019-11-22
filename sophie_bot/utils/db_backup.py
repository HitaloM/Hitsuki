# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from datetime import datetime

from sophie_bot.config import get_str_key
from sophie_bot.services.mongo import MONGO_URI
from sophie_bot.utils.logger import log
from sophie_bot.utils.term import term

BACKUP_DIR = 'Backups'


def backup_db(prefix='', postfix=''):
    log.warning('Backuping DB...')
    term(f'mongodump --uri {MONGO_URI} --out {BACKUP_DIR}/temp_dir')
    date_str = datetime.now().strftime("%d-%m-%Y=%H:%M:%S")
    term(f'cd {BACKUP_DIR} && 7z a "bac_{prefix}{date_str}{postfix}.zip" temp_dir/* -p{get_str_key("BACKUP_PASS")}')
    term(f'rm -rf {BACKUP_DIR}/temp_dir')
    log.info('Backup done!')
