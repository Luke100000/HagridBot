import asyncio
import random

import discord
from discord import File, Message

from app import config
from app.modules.config import retrieve
from app.modules.paint import paint
from app.modules.sirben import SIRBEN_VERSES
from app.modules.talk import speak
from app.stats import stat, stats

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.voice_states = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    whitelisted = message.guild.id in config.settings.whitelisted_guilds

    msg = message.content.lower().replace(",", "")

    for trigger, response in config.settings.triggers.items():
        for variant in trigger.split("|"):
            all_matched = True
            for word in variant.split("&"):
                if word not in msg:
                    all_matched = False
                    break
            if all_matched:
                await message.channel.send(response)
                stat(message, f"trigger: {trigger}")
                return

    if "sirben" in msg:
        stat(message, "sirben")
        verse = random.randrange(len(SIRBEN_VERSES))
        await message.channel.send(
            f"The Book of the Sirbens, chapter {verse % 30 + 1}, verse {verse % 17 + 1}:\n> {SIRBEN_VERSES[verse]}"
        )

    elif "hagrid help" in msg:
        stat(message, "help")
        text = "\n".join(
            [
                "Oi there!",
                "* `hagrid paint <prompt>` and I'll whip up a painting for ya, in me own style.",
                "* `hagrid draw <prompt>` if ya fancy, but if ya don't like me style, I'll ask a mate to have a go at it.",
                "* `hey hagrid <prompt>` if ya got a question. I'll give it me best shot at answerin'.",
            ]
        )
        await message.channel.send(text)

    elif "hagrid config" in msg:
        stat(message, "config")
        await message.channel.typing()
        await message.channel.send(await retrieve(msg.replace("config", "").strip()))

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

    elif (
        message.guild.id in config.settings.whitelisted_guilds
        and ("hagrid paint" in msg or "hagrid draw" in msg)
        and len(msg) > 15
    ):
        await message.channel.send("Alright, give me a few seconds!")
        await message.channel.typing()
        path = await asyncio.to_thread(
            paint,
            f"{msg.replace('hagrid paint', '').replace('hagrid draw', '').strip()}"
            + (", oil painting with impasto" if "paint" in msg else "")
            + " masterpiece, highly detailed, 8k",
        )
        await message.channel.send("Here, I hope you like it!", file=File(path))

    elif whitelisted and "hagrid usage stats" in msg:
        characters = 80
        lines = [
            "Thi's 'ere's th' usage stats 'cross all th' guilds I'm on:",
            "```md",
        ]
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

    elif (
        "hey hagrid" in msg
        or "hi hagrid" in msg
        or "hello hagrid" in msg
        or "hallo hagrid" in msg
    ):
        stat(message, "hey hagrid")
        await message.channel.typing()
        await message.channel.send(await speak(message))


if __name__ == "__main__":
    client.run(config.TOKEN)
