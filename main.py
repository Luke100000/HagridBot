import os
import random

import discord
from dotenv import load_dotenv

from config import retrieve
from hagrid import hagrid
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

    elif "hagrid config" in msg:
        await message.channel.send(retrieve(msg.replace("config", "")))

    elif "polygamy" in msg:
        await message.channel.send(
            f"Polygamy deconfirmed part {random.randrange(1000) + 50}"
        )

    elif "league" in msg:
        await message.channel.send(f"Blimey, take a gander at this fella... We should ban 'im, we should.")

    elif "hagrid log" in msg:
        await message.channel.send(
            f"Oi! Jus' drop the latest.log 'ere. It be in yer Minecraft's save directory in logs. An' if ye be on a server, drop that log too. The crashlog don't always 'ave enough info. If ye wants to make sure ye don't get ignored, make a GitHub issue. An' if ye don't follow the template, I'll break yer kneecap, I will!"
        )

    elif "hagrid skins" in msg:
        await message.channel.send(
            f"Oi! Take a gander at this 'ere: https://github.com/Luke100000/minecraft-comes-alive/wiki/Custom-Skins"
        )

    elif "hey hagrid" in msg:
        await message.channel.send(hagrid(msg))


client.run(TOKEN)
