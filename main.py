import os
import random

import discord
from dotenv import load_dotenv

from config import retrieve
from hagrid import hagrid
from library import library
from sirben import SIRBEN_VERSES

import shelve


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

client = discord.Client(intents=intents)


stats = shelve.open("stats")


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
        await message.channel.send(
            """
Oh, blimey! I can't believe me ears, I really can't! What's the world come to when people start requestin' Minecraft Bedrock support for Minecraft Java, eh? It's like mixin' potions that should never be mixed! It's like tryin' to put a hippogriff in a teacup!

Minecraft Java and Bedrock are like two different magical creatures, they are! They've got their own spells, their own enchantments, and their own way of doin' things. It's like tryin' to teach a Hungarian Horntail ballet – it just ain't natural!

Minecraft Java is the original, the OG version, with all its glorious mods and customizability. It's like a finely brewed potion with all the ingredients carefully measured. But now, folks want to mix it with Bedrock, which is like tryin' to put a blast-ended skrewt in a tutu! It'll be messy, it will!

And don't even get me started on the technical side of things! It's like tryin' to tame a blast-ended skrewt – it's a wild mess! The codes, the compatibility issues, it's like puttin' a Niffler in a treasure room and expectin' it not to cause chaos!

I'm all for a bit of magical experimentation, but some things just shouldn't be tampered with, and mixin' Java and Bedrock is one of 'em! It's like tryin' to teach a Thestral how to dance the tango – it's just not meant to be!

So, let's keep things as they are, shall we? Let Java be Java, and Bedrock be Bedrock, and let's not go mixin' potions that could explode in our faces! Stick to the magic you know, and let's enjoy each version for what it is – a magical adventure in its own right!
            """
        )

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
        l = library()

        await message.channel.send(l)

    elif "hey hagrid" in msg:
        stat(message, "hey hagrid")
        await message.channel.typing()
        await message.channel.send(hagrid(msg))


client.run(TOKEN)
