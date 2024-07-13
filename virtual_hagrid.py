import discord
from discord import Message, Member, VoiceState
from discord.channel import VoiceChannel, TextChannel
from discord.ext import listening

from common import config
from modules.virtual_hagrid.talker import Talker
from modules.virtual_hagrid.thinker import Thinker
from modules.virtual_hagrid.transcriber import TranscriberSink

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.voice_states = True

client = discord.Client(intents=intents)

process_pool = listening.AudioProcessPool(1)


@client.event
async def on_ready():
    print(f"{client.user}'voice has connected to Discord!")
    print("Loading tts...")
    Talker.preload()
    print("TTS loaded!")


class HagridAttention:
    """
    An attention is one session, with its memory and listener.
    """

    _attentions: dict[listening.VoiceClient, "HagridAttention"] = {}

    def __init__(self, channel: VoiceChannel, voice_client: listening.VoiceClient):
        self.voice_client = voice_client

        self.talker = Talker(self.voice_client)
        self.thinker = Thinker(self.talker)

        voice_client.listen(
            TranscriberSink(self.thinker, voice_client),
            process_pool,
            channel=channel,
        )

    @staticmethod
    def get_attention(channel: VoiceChannel, voice_client: listening.VoiceClient):
        if voice_client not in HagridAttention._attentions:
            HagridAttention._attentions[voice_client] = HagridAttention(
                channel, voice_client
            )
        return HagridAttention._attentions[voice_client]

    @staticmethod
    async def refresh_attentions():
        for c in list(HagridAttention._attentions.keys()):
            if len(c.channel.members) <= 1:
                await c.disconnect(force=True)
                del HagridAttention._attentions[c]


async def join_channel(
    voice_channel: VoiceChannel, message_channel: TextChannel = None
):
    try:
        voice_client = await voice_channel.connect(cls=listening.VoiceClient)
    except discord.errors.ClientException:
        if message_channel is not None:
            await message_channel.send("I'm already here!")
        return

    HagridAttention.get_attention(voice_channel, voice_client)


@client.event
async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState):
    if not config.DEBUG and member.guild.id in config.WHITELISTED_GUILDS:
        return

    if before.channel is None and after.channel is not None:
        print(f"{member} joined voice channel {after.channel.name}")
        await join_channel(after.channel)

    if before.channel is not None and after.channel is None:
        print(f"{member} left voice channel {before.channel.name}")

        await HagridAttention.refresh_attentions()


@client.event
async def on_message(message: Message):
    if not config.DEBUG and message.guild.id in config.WHITELISTED_GUILDS:
        return

    if message.content == "hagrid join":
        if message.author.voice:
            await join_channel(message.author.voice.channel, message.channel)
        else:
            await message.channel.send(
                "Blimey, yer not in one of them voice channels, are ye?"
            )


if __name__ == "__main__":
    client.run(config.TOKEN)
