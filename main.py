import asyncio
import os
import random

import discord
from discord import Message, File
from dotenv import load_dotenv

from modules.config import retrieve
from data import HAGRID_BEDROCK
from modules.hagrid import hagrid
from modules.library import library
from modules.paint import paint
from modules.role_sync import role_sync_command, sync_users
from modules.sirben import SIRBEN_VERSES
from modules.smart_hagrid import on_smart_message
from stats import stat, stats

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DEBUG = bool(os.getenv("HAGRID_DEBUG"))

intents = discord.Intents.default()

intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

WHITELISTED_GUILDS = [747184859386085380, 1008386913889177710, 697239211237179414]


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_interaction(interaction):
    await role_sync_command(interaction)


@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    if (
        not DEBUG
        and message.guild.id in WHITELISTED_GUILDS
        and await on_smart_message(message)
    ):
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

    elif len(message.attachments) > 0:
        for attachment in message.attachments:
            if (
                attachment.content_type is not None
                and attachment.content_type.startswith("text/plain")
            ):
                if "Mod ID: 'architectury', Requested by: 'mca', Expected range: '" in (
                    await attachment.read()
                ).decode("utf-8"):
                    await message.channel.send(
                        "https://fontmeme.com/permalink/231105/b48ffbb9d6b7bc89c6ded7aa0826a1a4.png"
                    )

    elif "error 1" in msg or "error code 1" in msg or "exit code 1" in msg:
        await message.channel.send(
            "https://fontmeme.com/permalink/231105/b48ffbb9d6b7bc89c6ded7aa0826a1a4.png"
        )

    elif (
        message.guild.id in WHITELISTED_GUILDS
        and "hagrid paint" in msg
        and len(msg) > 15
    ):
        await message.channel.send("Alright, give me a few seconds!")
        await asyncio.to_thread(paint, msg.replace("hagrid paint", "").strip())
        await message.channel.send(
            "Here, I hope you like it!", file=File("image.jpg")
        )

    elif "hagrid skins" in msg:
        stat(message, "skins")
        await message.channel.send(
            f"Oi! Take a gander at this 'ere: https://github.com/Luke100000/minecraft-comes-alive/wiki/Custom-Skins"
        )

    elif message.guild.id in WHITELISTED_GUILDS and "hagrid usage stats" in msg:
        characters = 80
        lines = ["Thi's 'ere's th' usage stats 'cross all th' guilds I'm on:", "```md"]
        for guild in sorted(list(stats.keys())):
            lines.append("# " + guild)
            characters += len(guild)

            # noinspection PyUnresolvedReferences
            for value in sorted(list(stats[guild].keys())):
                # noinspection PyUnresolvedReferences
                line = f"* {value}: {stats[guild][value]}"
                lines.append(line.replace("_", " ").replace("*", " "))
                characters += len(line)

            if characters > 600:
                characters = 0
                lines.append("```")
                await message.channel.send("\n".join(lines))
                lines = ["```md"]
            else:
                lines.append("")
        lines.append("```")

        await message.channel.send("\n".join(lines))

    elif "hagrid skin library" in msg:
        await message.channel.send(library())

    elif "hey hagrid" in msg:
        stat(message, "hey hagrid")
        await message.channel.typing()
        await message.channel.send(hagrid(msg))

    await sync_users(message)


client.run(TOKEN)
