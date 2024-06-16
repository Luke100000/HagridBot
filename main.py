import asyncio
import random

import discord
from discord import Message, File

from common import config
from common.data import HAGRID_BEDROCK
from modules.config import retrieve
from modules.hagrid import hagrid
from modules.library import library
from modules.paint import paint
from modules.role_sync import role_sync_command, sync_users
from modules.sirben import SIRBEN_VERSES
from modules.smart_hagrid import on_smart_message
from common.stats import stat, stats

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.voice_states = True

client = discord.Client(intents=intents)


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
            not config.DEBUG
            and message.guild.id in config.WHITELISTED_GUILDS
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

    elif "hagrid help" in msg:
        stat(message, "help")
        text = "\n".join(
            [
                "Oi there!",
                "* `hagrid paint <prompt>` and I'll whip up a painting for ya, in me own style.",
                "* `hagrid draw <prompt>` if ya fancy, but if ya don't like me style, I'll ask a mate to have a go at it.",
                "* `hey hagrid <prompt>` if ya got a question. I'll give it me best shot at answerin'.",
                "* `hallo hagrid <prompt>` to start a chat. But I'll only be listenin' with one ear. Stick to 'Hey hagrid' for quick questions.",
                "* `bye hagrid` if ya want me to stop jabberin'."
            ])
        await message.channel.send(text)

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

    elif "hagrid in pain" in msg:
        await message.channel.send(
            "https://cdn.discordapp.com/attachments/1132232705157906433/1188842849161183232/pain.mp4?ex=659bff2e&is=65898a2e&hm=644a4a1981e8d4557c2b3488fdf333400cc9670079a3d266ec625f3cef84fd87&")

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
            message.guild.id in config.WHITELISTED_GUILDS
            and "hagrid paint" in msg
            and len(msg) > 15
    ):
        await message.channel.send("Alright, give me a few seconds!")
        await asyncio.to_thread(paint,
                                f"{msg.replace('hagrid paint', '').strip()}, drawn by Hagrid Rubeus, oil painting with impasto")
        await message.channel.send(
            "Here, I hope you like it!", file=File("image.webp")
        )

    elif (
            message.guild.id in config.WHITELISTED_GUILDS
            and "hagrid draw" in msg
            and len(msg) > 15
    ):
        await message.channel.send("Alright, give me a few seconds!")
        await asyncio.to_thread(paint, msg.replace("hagrid draw", "").strip())
        await message.channel.send(
            "Here, I hope you like it!", file=File("image.webp")
        )

    elif "hagrid skins" in msg:
        stat(message, "skins")
        await message.channel.send(
            f"Oi! Take a gander at this 'ere: https://github.com/Luke100000/minecraft-comes-alive/wiki/Custom-Skins"
        )

    elif message.guild.id in config.WHITELISTED_GUILDS and "hagrid usage stats" in msg:
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
        await message.channel.send(await hagrid(msg))

    await sync_users(message)


if __name__ == "__main__":
    client.run(config.TOKEN)
