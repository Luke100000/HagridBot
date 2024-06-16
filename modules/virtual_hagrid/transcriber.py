import threading
from collections import defaultdict

from discord.ext.listening import RTCPPacket, AudioFrame, AudioSink

from common.whisper_online import *
from modules.virtual_hagrid.thinker import Thinker

asr = FasterWhisperASR("en", "medium")

class Transcriber:
    def __init__(self, thinker: Thinker):
        self.processor = OnlineASRProcessor(asr)
        self.buffer = ""
        self.chunk_inserted = False
        self.end_reached = False
        self.last_processing = 0
        self.last_insertion = 0
        self.username = "Unknown"

        self.thinker = thinker

        self.thread = threading.Thread(target=self.sync, daemon=True)
        self.thread.start()

    def insert_message(self, message: str):
        self.buffer += message

        if message:
            print(f"  {self.username} is saying: ...{message}...")

        has_point = ("." in self.buffer) or ("!" in self.buffer) or ("?" in self.buffer)
        if time.time() - self.last_insertion > (0.5 if has_point else 2.0) and self.buffer:
            self.thinker.add_message(self.username, self.buffer)
            self.buffer = ""

        if message:
            self.last_insertion = time.time()
            self.thinker.heard_something()

    def sync(self):
        while True:
            if (self.chunk_inserted or not self.end_reached) and time.time() - self.last_processing > 2.0:
                _, _, text = self.processor.process_iter()
                if text:
                    self.insert_message(text)

                if self.chunk_inserted:
                    self.chunk_inserted = False
                else:
                    self.end_reached = True
                self.last_processing = time.time()

            self.insert_message("")
            time.sleep(0.01)

    def insert_audio_chunk(self, resampled_audio):
        self.processor.insert_audio_chunk(resampled_audio)
        self.chunk_inserted = True
        self.end_reached = False

    def set_username(self, username):
        self.username = username

class WhisperSink(AudioSink):
    def __init__(self, thinker: Thinker):
        super().__init__()

        self.thinker = thinker

        self.transcribers = defaultdict(lambda: Transcriber(self.thinker))

    def on_audio(self, frame: AudioFrame) -> None:
        if frame.user:
            chunk = frame.audio
            raw_audio, sr = sf.read(io.BytesIO(chunk), format="RAW", subtype="PCM_16", channels=2, samplerate=48000)
            resampled_audio = raw_audio[::3, :].mean(1)
            self.transcribers[frame.user.id].insert_audio_chunk(resampled_audio)
            self.transcribers[frame.user.id].set_username(frame.user.display_name)

    def on_rtcp(self, packet: RTCPPacket) -> None:
        pass

    def cleanup(self) -> None:
        pass
