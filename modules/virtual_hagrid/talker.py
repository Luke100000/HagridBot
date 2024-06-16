import asyncio
import threading

from TTS.api import TTS
from discord import opus, SpeakingState
from discord.ext import listening

from common.utils import byteFIFO
from common.whisper_online import *


class Talker:
    model = None
    gpt_cond_latent = None
    speaker_embedding = None

    @staticmethod
    def preload():
        Talker.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        Talker.model.to("cuda")

        (
            Talker.gpt_cond_latent,
            Talker.speaker_embedding,
        ) = Talker.model.synthesizer.tts_model.get_conditioning_latents(
            audio_path=[
                "data/0.wav",
                "data/1.wav",
                "data/2.wav",
                "data/3.wav",
                "data/4.wav",
                "data/5.wav",
                "data/6.wav",
                "data/7.wav",
                "data/8.wav",
                "data/9.wav",
            ]
        )

    def __init__(self, vc: listening.VoiceClient):
        self.queue = []
        self.talking = False
        self.vc = vc

        self.sync_thread = threading.Thread(target=self.talk, daemon=True)
        self.sync_thread.start()

    def generate_audio(self, text: str):
        frame = self.vc.encoder.FRAME_SIZE

        print("Hagrid talks:", text)

        chunks = Talker.model.synthesizer.tts_model.inference_stream(
            text, "en", self.gpt_cond_latent, self.speaker_embedding
        )

        buffer = byteFIFO()
        for i, chunk in enumerate(chunks):
            audio = chunk.squeeze().unsqueeze(0).cpu().numpy()[0]
            resampled_audio = librosa.resample(audio, orig_sr=24000, target_sr=48000, res_type="linear")
            resampled_audio = np.stack((resampled_audio,) * 2, axis=1)

            data = (resampled_audio * 32767).astype(np.int16).tobytes()
            buffer.put(data)

            while len(buffer) >= frame:
                yield buffer.get(frame)

        yield buffer.get(frame)

    def talk(self):
        while True:
            if self.queue:
                text = self.queue.pop(0)

                if text:
                    self.set_talking(True)

                    last_talk = time.time()
                    frame = 0
                    buffer = 0.1

                    if not self.vc.encoder:
                        self.vc.encoder = opus.Encoder()

                    for chunk in self.generate_audio(text):
                        if chunk:
                            delta = time.time() - last_talk
                            target_time = frame * 0.02 - buffer
                            if target_time > delta:
                                time.sleep(target_time - delta)
                            self.vc.send_audio_packet(chunk)
                            frame += 1

                    self.set_talking(False)
            else:
                time.sleep(0.1)

    def speak(self, text: str):
        self.queue.append(text)

    def set_talking(self, talking: bool):
        self.talking = talking
        asyncio.run_coroutine_threadsafe(
            self.vc.ws.speak(
                SpeakingState.voice if self.talking else SpeakingState.none
            ),
            self.vc.client.loop,
        )
