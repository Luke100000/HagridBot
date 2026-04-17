import asyncio
import random

import discord
from discord import File, Message, app_commands

from app import config
from app.modules.config import retrieve
from app.modules.crosspost import CrosspostGuard
from app.modules.paint import paint
from app.modules.ranks import RankModule
from app.modules.sirben import SIRBEN_VERSES
from app.modules.talk import speak
from app.stats import StatsModule, stat
from app.storage import init_storage


class HagridClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self._crosspost_guard = CrosspostGuard()
        self._ranks_module = RankModule(self, self.tree)
        self._stats_module = StatsModule(self.tree)

    async def setup_hook(self) -> None:
        init_storage()
        await self._ranks_module.setup()
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"{self.user} has connected to Discord!")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return
        if message.author.bot:
            return
        if message.guild is None:
            return

        # Normalize the message content
        attachment_count = len(message.attachments)
        normalized = " ".join(message.content.lower().replace(",", "").split())
        if attachment_count > 0:
            normalized += f" attachments:{attachment_count}"

        whitelisted = message.guild.id in config.settings.whitelisted_guilds

        # Crossposting
        if await self._crosspost_guard.handle(message, normalized, self):
            return

        await self._ranks_module.handle_message_xp(message, normalized)

        # Basic triggers
        for trigger, response in config.settings.triggers.items():
            for variant in trigger.split("|"):
                all_matched = True
                for word in variant.split("&"):
                    if word not in normalized:
                        all_matched = False
                        break
                if all_matched:
                    await message.channel.send(response)
                    stat(message, f"trigger: {trigger}")
                    return

        if message.channel.name == "sus":
            stat(message, "sus")
            await message.channel.send(
                f"Oi <@{message.author.id}>, caught you yapperin’ in here, so I gave ya a friendly chat with me boots an’ sent ya hobblin’ out the door."
            )
            if not message.author.top_role.permissions.administrator:
                await message.author.ban(
                    delete_message_seconds=60,
                    reason="Talking in the sus channel, as per Hagrid's orders.",
                )
                await message.author.unban()

        elif "sirben" in normalized:
            stat(message, "sirben")
            verse = random.randrange(len(SIRBEN_VERSES))
            await message.channel.send(
                f"The Book of the Sirbens, chapter {verse % 30 + 1}, verse {verse % 17 + 1}:\n> {SIRBEN_VERSES[verse]}"
            )

        elif "hagrid help" in normalized:
            stat(message, "help")
            text = "\n".join(
                [
                    "Oi there!",
                    "* `hagrid paint <prompt>` and I'll whip up a painting for ya, in me own style.",
                    "* `hagrid draw <prompt>` if ya fancy, but if ya don't like me style, I'll ask a mate to have a go at it.",
                    "* `hey hagrid <prompt>` if ya got a question. I'll give it me best shot at answerin'.",
                    "* `hagrid config <prompt>` if ya wanna know how to configure MCA. I'll fetch the info for ya.",
                ]
            )
            await message.channel.send(text)

        elif "hagrid config" in normalized:
            stat(message, "config")
            await message.channel.typing()
            await message.channel.send(
                await retrieve(normalized.replace("config", "").strip())
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

        elif (
            whitelisted
            and ("hagrid paint" in normalized or "hagrid draw" in normalized)
            and len(normalized) > 15
        ):
            await message.channel.send("Alright, give me a few seconds!")
            await message.channel.typing()
            path = await asyncio.to_thread(
                paint,
                f"{normalized.replace('hagrid paint', '').replace('hagrid draw', '').strip()}"
                + (", oil painting with impasto" if "paint" in normalized else "")
                + " masterpiece, highly detailed, 8k",
            )
            await message.channel.send("Here, I hope you like it!", file=File(path))

        elif (
            "hey hagrid" in normalized
            or "hi hagrid" in normalized
            or "hello hagrid" in normalized
            or "hallo hagrid" in normalized
        ):
            stat(message, "hey hagrid")
            await message.channel.typing()
            await message.channel.send(await speak(message))




if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    client = HagridClient(intents=intents)
    client.run(config.TOKEN)
