import asyncio
import subprocess

from sophie_bot.services.telethon import tbot


async def chat_term(message, command):
	result = await term(command)
	if len(result) > 4096:
		output = open("output.txt", "w+")
		output.write(result)
		output.close()
		await tbot.send_file(
			message.chat.id,
			"output.txt",
			reply_to=message['message_id'],
			caption="`Output too large, sending as file`",
		)
		subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
	return result


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
