import discord
from discord import Message
from discord.channel import VocalGuildChannel
from discord.ext import listening

from common import config
from modules.virtual_hagrid.talker import Talker
from modules.virtual_hagrid.thinker import Thinker
from modules.virtual_hagrid.transcriber import WhisperSink

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


@client.event
async def on_voice_state_update(member, before, after):
    print(member, before, after)


class HagridAttention:
    _attentions = {}

    def __init__(self, channel: VocalGuildChannel, voice_client: listening.VoiceClient):
        self.voice_client = voice_client

        self.talker = Talker(self.voice_client)
        self.thinker = Thinker(self.talker)

        voice_client.listen(
            WhisperSink(self.thinker),
            process_pool,
            after=on_listen_finish,
            channel=channel
        )

    @staticmethod
    def get_attention(channel: VocalGuildChannel, voice_client: listening.VoiceClient):
        if voice_client not in HagridAttention._attentions:
            HagridAttention._attentions[voice_client] = HagridAttention(channel, voice_client)
        return HagridAttention._attentions[voice_client]


@client.event
async def on_message(message: Message):
    if (
            not config.DEBUG
            and message.guild.id in config.WHITELISTED_GUILDS
    ):
        return

    if message.content == "hagrid join":
        if message.author.voice:
            try:
                channel = message.author.voice.channel
                voice_client = await channel.connect(cls=listening.VoiceClient)
            except discord.errors.ClientException:
                await message.channel.send("I'm already here!")
                return

            HagridAttention.get_attention(channel, voice_client)
        else:
            await message.channel.send("Blimey, yer not in one of them voice channels, are ye?")


def on_listen_finish():
    print("Listening finished")


if __name__ == "__main__":
    client.run(config.TOKEN)
