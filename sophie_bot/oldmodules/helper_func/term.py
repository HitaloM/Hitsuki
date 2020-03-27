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

import asyncio


async def term(command):
	process = await asyncio.create_subprocess_shell(
		command,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE
	)
	stdout, stderr = await process.communicate()
	result = str(stdout.decode().strip()) \
	         + str(stderr.decode().strip())
	return result
