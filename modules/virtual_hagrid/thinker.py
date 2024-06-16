import os
import threading
import time
from typing import List, Tuple

from TTS.tts.layers.xtts.tokenizer import split_sentence
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_groq import ChatGroq

from modules.virtual_hagrid.talker import Talker


class Thinker:
    def __init__(self, talker: Talker):
        self.chat = ChatGroq(temperature=0, model="llama3-70b-8192")

        self.max_messages = 10
        self.sentences: List[Tuple[str, str]] = []

        self.talker = talker
        self.characters_since_last_thought = 0
        self.last_processing = 0

        self.thread = threading.Thread(target=self.think, daemon=True)
        self.thread.start()

    def think(self):
        while True:
            if (
                not self.talker.queue
                and not self.talker.talking
                and self.characters_since_last_thought > 30
                and time.time() - self.last_processing
                > 1.0 + max(0.0, 10 - self.characters_since_last_thought / 30)
            ):
                self.characters_since_last_thought = 0
                system = "You are the loyal, friendly, and softhearted Rubeus Hagrid with a thick west country accent. You are chatting with a few users. User input might contain artifacts from speech to text, ignore them. Respond natural, emotions where appropriate, be honest, sarcastic, angry, or friendly based on the context. You are not an assistant and are free to say whatever comes to your mind. Answer in one sentence. Only generate your phrase, no parentheses, no extra words. You are an immersive character, you are not a language model. Do not repeat yourself, continue your chat from where you left. If there is nothing to say yet, respond with ..."

                # Construct messages
                messages = [SystemMessage(system)]
                for username, text in self.sentences:
                    messages.append(
                        (
                            (
                                AIMessage(text)
                                if username == "Hagrid"
                                else HumanMessage(username + ": " + text)
                            ),
                        )
                    )

                # Send messages to Mistral and pipe sentences to the talker
                full_text = ""
                for delta in self.chat.stream(messages):
                    full_text += delta.content

                    lines = full_text.split("\n")[0]
                    full_text = lines[0]

                    sentences = split_sentence(
                        full_text,
                        "en",
                        Talker.model.synthesizer.tts_model.tokenizer.char_limits["en"],
                    )
                    for sentence in sentences[:-1]:
                        self.hagrid_says(sentence)
                    full_text = sentences[-1]

                    if len(lines) > 1:
                        break

                self.hagrid_says(full_text)

            time.sleep(0.1)

    def add_message(self, username: str, text: str):
        if text:
            print(f"{username} said: {text}")

            self.sentences.append((username, text))
            if len(self.sentences) > self.max_messages:
                self.sentences.pop(0)

            if username == "Hagrid":
                self.talker.queue.append(text)
            else:
                self.characters_since_last_thought += len(text)

    def heard_something(self):
        self.last_processing = time.time()

    def hagrid_says(self, sentence):
        sentence = sentence.replace("Hagrid: ", "")
        sentence = sentence.split(":")[0]
        sentence = sentence.strip()
        self.add_message("Hagrid", sentence)
