import os
import random

import discord
from dotenv import load_dotenv

from config import retrieve
from data import HAGRID_BEDROCK
from hagrid import hagrid
from library import library
from sirben import SIRBEN_VERSES

import shelve

from smart_hagrid import on_smart_message

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

client = discord.Client(intents=intents)


os.makedirs("shelve/", exist_ok=True)

stats = shelve.open("shelve/stats")


def stat(message, typ):
    guild = message.guild.name
    if guild in stats:
        g: dict = stats[guild]
        if typ in g:
            g[typ] += 1
        else:
            g[typ] = 1
        stats[guild] = g
    else:
        stats[guild] = {typ: 1}
    stats.sync()


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if await on_smart_message(message):
        return

    msg = message.content.lower()

    if "sirben" in msg:
        stat(message, "sirben")
        verse = random.randrange(len(SIRBEN_VERSES))
        await message.channel.send(
            f"The Book of the Sirbens, chapter {verse % 30 + 1}, verse {verse % 17 + 1}:\n> {SIRBEN_VERSES[verse]}"
        )

    elif "hagrid config" in msg:
        stat(message, "config")
        await message.channel.send(retrieve(msg.replace("config", "")))

    elif "polygamy" in msg:
        stat(message, "polygamy")
        await message.channel.send(
            f"Polygamy deconfirmed part {random.randrange(1000) + 50}"
        )

    elif "port" in msg and "1.12" in msg:
        stat(message, "1.12")
        await message.channel.send(
            f"Ah, blimey! This MCA 1.12.2 port, it's a right headache, I'm tellin' ya! All them technical tweaks and compatibility fuss, it's a right bunch of unnecessary work, ain't it?"
        )

    elif "league" in msg:
        stat(message, "league")
        await message.channel.send(
            f"Blimey, take a gander at this fella... We should ban 'im, we should."
        )

    elif "bedrock intensifies" in msg:
        stat(message, "bedrock_intensifies")
        await message.channel.send(HAGRID_BEDROCK)

    elif "bedrock" in msg:
        stat(message, "bedrock_intensifies")
        await message.channel.send(
            """By the stars above, don't you see? Minecraft Java and Bedrock are like two entirely different worlds – their architectures are as distant as a Thestral and a Niffler! It's a maddening notion to even think about mixin' 'em, like tryin' to merge dragons and pixies!"""
        )

    elif "hagrid log" in msg:
        stat(message, "log")
        await message.channel.send(
            f"Oi! Jus' drop the latest.log 'ere. It be in yer Minecraft's save directory in logs. An' if ye be on a server, drop that log too. The crashlog don't always 'ave enough info. If ye wants to make sure ye don't get ignored, make a GitHub issue. An' if ye don't follow the template, I'll break yer kneecap, I will!"
        )

    elif "hagrid skins" in msg:
        stat(message, "skins")
        await message.channel.send(
            f"Oi! Take a gander at this 'ere: https://github.com/Luke100000/minecraft-comes-alive/wiki/Custom-Skins"
        )

    elif "hagrid usage stats" in msg:
        lines = ["Thi's 'ere's th' usage stats 'cross all th' guilds I'm on:", "```md"]
        for guild in sorted(list(stats.keys())):
            lines.append("# " + guild)
            # noinspection PyUnresolvedReferences
            for value in sorted(list(stats[guild].keys())):
                # noinspection PyUnresolvedReferences
                lines.append(f"* {value}: {stats[guild][value]}")
            lines.append("")
        lines.append("```")

        await message.channel.send("\n".join(lines))

    elif "hagrid skin library" in msg:
        await message.channel.send(library())

    elif "hey hagrid" in msg:
        stat(message, "hey hagrid")
        await message.channel.typing()
        await message.channel.send(hagrid(msg))


client.run(TOKEN)
