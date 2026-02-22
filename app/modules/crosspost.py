import discord
from discord import Message


class CrosspostGuard:
    def __init__(self):
        # user_id -> (normalized_content, channel_id, message_id)
        self._last_message_by_user = {}

    async def handle(
        self, message: Message, normalized: str, client: discord.Client
    ) -> bool:
        if not normalized:
            return False

        last = self._last_message_by_user.get(message.author.id)
        if last is not None:
            last_content, last_channel_id, last_message_id = last
            if normalized == last_content and message.channel.id != last_channel_id:
                await message.channel.send(
                    f"Oi <@{message.author.id}>, quit spamming 'cross channels, I booted it out meself."
                )

                # Best-effort delete both messages, then kick.
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

                try:
                    last_channel = client.get_channel(last_channel_id)
                    if last_channel is not None:
                        last_message = await last_channel.fetch_message(last_message_id)
                        await last_message.delete()
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    pass

                try:
                    await message.guild.kick(
                        message.author,
                        reason="Crosspost spam detected by Hagrid.",
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                self._last_message_by_user.pop(message.author.id, None)
                return True

        self._last_message_by_user[message.author.id] = (
            normalized,
            message.channel.id,
            message.id,
        )
        return False
