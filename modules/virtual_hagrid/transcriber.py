import io
import threading
from collections import defaultdict

import soundfile
from discord.ext import listening
from discord.ext.listening import RTCPPacket, AudioFrame, AudioSink

from common.whisper_online import *
from modules.virtual_hagrid.thinker import Thinker

asr = FasterWhisperASR("en", "medium")


class Transcriber:
    """
    Transcribers processes audio per user and maintain the current speaking state.
    Once a sentence has been detected, it is forwarded to the thinker.
    """

    def __init__(self, thinker: Thinker, voice_client: listening.VoiceClient):
        self.processor = OnlineASRProcessor(asr)
        self.buffer = ""
        self.chunk_inserted = False
        self.last_processing = 0
        self.last_insertion = 0
        self.username = "Unknown"

        self.min_chunk_size = 1.0

        self.thinker = thinker
        self.voice_client = voice_client

        self.thread = threading.Thread(target=self.sync, daemon=True)
        self.thread.start()

    def sync(self):
        while self.voice_client.is_connected():
            if time.time() - self.last_processing > self.min_chunk_size:
                if not self.chunk_inserted:
                    self.processor.insert_audio_chunk(
                        np.zeros((int(16000 * self.min_chunk_size),), dtype=np.float32)
                    )
                    print("added silence")

                _, _, text = self.processor.process_iter()
                if text:
                    self.insert_message(text)
                else:
                    print("silence")

                self.chunk_inserted = False
                self.last_processing = time.time()

            self.insert_message("")
            time.sleep(0.01)

    def insert_message(self, message: str):
        self.buffer += message

        if message:
            print(f"  {self.username} is saying: ...{message}...")

        # If there is some silent, commit this as a message
        has_point = ("." in self.buffer) or ("!" in self.buffer) or ("?" in self.buffer)
        if (
            time.time() - self.last_insertion > (0.5 if has_point else 2.0)
            and self.buffer
        ):
            self.thinker.add_message(self.username, self.buffer)
            self.buffer = ""

        # Let the thinker know that we heard something
        if message:
            self.last_insertion = time.time()
            self.thinker.heard_something()

    def insert_audio_chunk(self, resampled_audio):
        self.processor.insert_audio_chunk(resampled_audio)
        self.chunk_inserted = True

    def set_username(self, username):
        self.username = username


class TranscriberSink(AudioSink):
    """
    The sink listens to user audio, converts it and forwards it to the transcriber.
    """

    def __init__(self, thinker: Thinker, voice_client: listening.VoiceClient):
        super().__init__()

        self.thinker = thinker

        self.transcribers = defaultdict(lambda: Transcriber(self.thinker, voice_client))

    def on_audio(self, frame: AudioFrame) -> None:
        if frame.user:
            chunk = frame.audio
            raw_audio, sr = soundfile.read(
                io.BytesIO(chunk),
                format="RAW",
                subtype="PCM_16",
                channels=2,
                samplerate=48000,
            )
            resampled_audio = raw_audio[::3, :].mean(1)
            self.transcribers[frame.user.id].insert_audio_chunk(resampled_audio)
            self.transcribers[frame.user.id].set_username(frame.user.display_name)

    def on_rtcp(self, packet: RTCPPacket) -> None:
        pass

    def cleanup(self) -> None:
        pass
