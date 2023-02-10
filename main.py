import os
import random

import discord
from dotenv import load_dotenv

from config import retrieve
from grumpy import grumpy
from sirben import SIRBEN_VERSES

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content.lower()

    if "sirben" in msg:
        verse = random.randrange(len(SIRBEN_VERSES))
        await message.channel.send(
            f"The Book of the Sirbens, chapter {verse % 30 + 1}, verse {verse % 17 + 1}:\n> {SIRBEN_VERSES[verse]}"
        )

    elif "hagrid" in msg and "config" in msg:
        await message.channel.send(retrieve(msg.replace("config", "")))

    elif "polygamy" in msg:
        await message.channel.send(
            f"Polygamy deconfirmed part {random.randrange(1000) + 50}"
        )

    elif "hagrid" in msg and "log" in msg:
        await message.channel.send(
            f"Drop the `latest.log` here. It's in your Minecraft's save directory in `logs`. If your are on a server, drop that log too. The crashlog does not always contain enough information. If you want to make sure to not get ignored, make a GitHub issue. And if you do not follow the template I will break you kneecap."
        )

    elif msg.startswith("hey hagrid"):
        await message.channel.send(grumpy(msg))


client.run(TOKEN)
