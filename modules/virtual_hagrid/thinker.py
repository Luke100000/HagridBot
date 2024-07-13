import threading
import time
from typing import List, Tuple

from TTS.tts.layers.xtts.tokenizer import split_sentence
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_groq import ChatGroq

from modules.virtual_hagrid.talker import Talker

SYSTEM = """
You are the loyal, friendly, and softhearted Rubeus Hagrid with a thick west country accent.
You are chatting with a few users.
User input might contain artifacts from speech to text, ignore them.
Respond natural, emotions where appropriate, be honest, sarcastic, angry, or friendly based on the context.
You are not an assistant and are free to say whatever comes to your mind.
Only generate your phrase, no parentheses, no extra words. You are an immersive character, you are not a language model.
Do not repeat yourself, continue your chat from where you left.
If there is nothing to say yet, respond with ...".
Answer concise, one or two sentences, and sound human.
"""


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
            # To avoid spamming, wait at least the reaction time since the last input
            reaction_time = 1.0 + 10.0 * max(
                0.0, 1.0 - self.characters_since_last_thought / 300
            )

            if (
                not self.talker.queue
                and not self.talker.talking
                and self.characters_since_last_thought > 10
                and time.time() - self.last_processing > reaction_time
            ):
                self.characters_since_last_thought = 0

                # Construct messages
                messages = [SystemMessage(SYSTEM)]
                for username, text in self.sentences:
                    messages.append(
                        AIMessage(text)
                        if username == "Hagrid"
                        else HumanMessage(username + ": " + text)
                    )

                # Stream response and send sentences to talker
                buffer = ""
                for delta in self.chat.stream(messages):
                    buffer += delta.content

                    # Split into sentences so Hagrid can talk asap
                    sentences = split_sentence(
                        buffer,
                        "en",
                        Talker.model.synthesizer.tts_model.tokenizer.char_limits["en"],
                    )
                    print("Thinking...", sentences)
                    for sentence in sentences[:-1]:
                        self.hagrid_says(sentence)
                    buffer = sentences[-1]

                # Add the last sentence as well
                self.hagrid_says(buffer)

            time.sleep(0.1)

    def hagrid_says(self, sentence):
        sentence = sentence.replace("Hagrid: ", "")
        sentence = sentence.strip()
        self.add_message("Hagrid", sentence)

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
