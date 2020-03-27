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

import time


def benchmark(func):
	async def wrapper(*args, **kwargs):
		start = time.time()
		return_value = await func(*args, **kwargs)
		end = time.time()
		print('[*] Time: {} sec.'.format(end - start))
		return return_value

	return wrapper
