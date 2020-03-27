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

from sophie_bot.services.mongo import mongodb
from sophie_bot.utils.logger import log

log.info('Sophie Database v3')
log.info('Support notes aliases')
log.info('Starting updating all notes...')

all_notes = mongodb.notes_v2.find({})
all_notes_count = all_notes.count()
counter = 0
changed_notes = 0
for note in all_notes:
	counter += 1
	log.info(f'Updating {counter} of {all_notes_count}...')

	if 'name' in note:
		changed_notes += 1
		names = [note['name']]
		del note['name']
		note['names'] = names
		mongodb.notes_v2.replace_one({'_id': note['_id']}, note)

log.info('Update done!')
log.info('Modified notes - ' + str(changed_notes))
log.info('Unchanged notes - ' + str(all_notes_count - changed_notes))
