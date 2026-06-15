import discord
from discord import Message


class CrosspostGuard:
    def __init__(self):
        # (guild_id, user_id) -> (normalized_content, consecutive_count)
        self._last_message_by_user = {}

    async def handle(self, message: Message, normalized: str) -> bool:
        if len(normalized) < 8:
            return False

        key = (message.guild.id, message.author.id)
        last = self._last_message_by_user.get(key)
        if last is not None:
            last_content, count = last
            if normalized == last_content:
                count += 1
                self._last_message_by_user[key] = (normalized, count)

                if count == 2:
                    try:
                        await message.channel.send(
                            f"Oi <@{message.author.id}>, Hagrid listens for duplicate messages. Send that same thing again and I'll boot ye out meself.",
                            delete_after=15,
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return True

                await message.channel.send(
                    f"Oi <@{message.author.id}>, that's enough spam. Out ye go."
                )

                try:
                    await message.guild.ban(
                        message.author,
                        delete_message_seconds=60,
                        reason="Spam detected by Hagrid.",
                    )
                    await message.author.unban()
                except (discord.Forbidden, discord.HTTPException):
                    pass
                self._last_message_by_user.pop(key, None)
                return True

        self._last_message_by_user[key] = (normalized, 1)
        return False
