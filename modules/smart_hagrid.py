import asyncio
import datetime
import json
import os
import random
import shelve
import sqlite3
from typing import List

import aiohttp
import pytz as pytz
from cache import AsyncLRU
from discord import Message, File
from groq.types.chat import ChatCompletionToolParam

from common.data import HAGRID_COMMANDS
from common.openai_utils import generate_text
from common.stats import stat
from modules.paint import paint

os.makedirs("shelve/", exist_ok=True)

progress = shelve.open("shelve/progress")
settings = shelve.open("shelve/settings")


con = sqlite3.connect("shelve/database.db")

FIXED_HISTORY_N = 2
MAX_HISTORY_N = 5
HISTORY_LENGTH = 2048
MAX_CONVERSATION_TIME = 100


def setup():
    con.execute(
        """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        guild INTEGER,
        channel INTEGER,
        author INTEGER,
        content TEXT,
        date DATETIME,
        indexed BOOLEAN
    )
    """
    )

    con.execute(
        """
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild INTEGER,
        channel INTEGER,
        from_date DATETIME,
        to_date DATETIME,
        summary TEXT
    )
    """
    )


setup()


active_conversations = {}


def drop_until(messages: List[str], max_size: int):
    while len(messages) > 0 and sum([len(m) for m in messages]) > max_size:
        messages.pop(random.randrange(len(messages)))
    return messages


@AsyncLRU(3600)
async def who_is(user_id, max_length=10_000):
    messages = con.execute(
        "SELECT content FROM messages WHERE author=? ORDER BY RANDOM() LIMIT 1000",
        (user_id,),
    ).fetchall()

    messages = [m[0] for m in messages if not m[0].startswith("/")]
    drop_until(messages, max_length)

    prompt = "> " + "\n> ".join(messages)

    print(f"Describing user with {len(messages)} messages and {len(prompt)} chars")

    system_prompt = "You are a language model tasked with describing this person in a few honest sentences, based on their past messages. Put focus on personality and behavior."
    return await generate_text(prompt, system_prompt=system_prompt, max_tokens=256)


def get_yesterday_boundary() -> (datetime, datetime):
    # Define the CEST timezone
    cest = pytz.timezone("Europe/Berlin")  # Central European Summer Time (CEST)

    # Get the current date and time in the CEST timezone
    now_cest = datetime.datetime.now(cest)

    # Set the time to 12:00 PM (noon)
    noon_cest = now_cest.replace(hour=12, minute=0, second=0, microsecond=0)

    # If the current time is before 12:00 PM, consider yesterday's boundary
    if now_cest < noon_cest:
        yesterday = noon_cest - datetime.timedelta(days=1)
    else:
        yesterday = noon_cest

    return yesterday - datetime.timedelta(days=1), yesterday


@AsyncLRU(3)
async def get_summary(guild_id, channel_id, offset: int = 0, max_length: int = 10_000):
    from_date, to_date = get_yesterday_boundary()
    from_date = from_date - datetime.timedelta(days=offset)
    to_date = to_date - datetime.timedelta(days=offset)

    summary = con.execute(
        "SELECT summary FROM summaries WHERE guild=? AND channel=? AND from_date=? AND to_date=?",
        (guild_id, channel_id, from_date, to_date),
    ).fetchone()

    if summary is None:
        messages = con.execute(
            """
            SELECT content, names.name as username
            FROM messages
            LEFT JOIN names ON names.id=messages.author
            WHERE guild=? AND (? < 0 OR channel=?) AND date BETWEEN ? AND ?
            """,
            (guild_id, channel_id, channel_id, from_date, to_date),
        ).fetchall()

        messages = [f"{m[1]}: {m[0]}" for m in messages if not m[0].startswith("/")]

        original_count = len(messages)

        # Crop to fit into context size
        messages = drop_until(messages, max_length)

        # Construct prompt
        prompt = "> " + "\n> ".join(messages)

        # No need to summarize a single message
        if len(prompt) < 64:
            return "Nothing.", from_date, to_date

        prompt = f"Today's new conversations:{prompt}\n\nToday's summary"

        # Generate summary
        where = (
            "public Discord server"
            if channel_id < 0
            else "specific Discord server channel"
        )
        system_prompt = f"You are a language model tasked with summarizing following conversation on a {where} in a concise way."
        summary = await generate_text(
            prompt,
            system_prompt=system_prompt,
            max_tokens=256,
            model="gpt-3.5-turbo",
            temperature=0.25,
        )

        # Cache summary
        con.execute(
            """
            INSERT INTO summaries (guild, channel, from_date, to_date, summary) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, channel_id, from_date, to_date, summary),
        )
        con.commit()

        print(
            f"Summarized day with {original_count} original, {len(messages)} compressed messages and {len(prompt)} chars."
        )

        return summary, from_date, to_date
    else:
        return summary[0], from_date, to_date


def set_index_status(channel_id, active: bool):
    if active:
        settings[str(channel_id)] = True
    else:
        del settings[str(channel_id)]

    con.execute(
        """
    UPDATE messages
    SET indexed=?
    WHERE channel=?
    """,
        (1 if active else 0, channel_id),
    )


async def track(message: Message):
    after = None
    if str(message.channel.id) in progress:
        after = progress[str(message.channel.id)]

    indexed = str(message.channel.id) in settings

    count = 0
    async for received in message.channel.history(
        limit=100, after=after, oldest_first=True
    ):
        if received.clean_content and not received.clean_content.startswith("/hagrid"):
            count += 1

            con.execute(
                "INSERT OR REPLACE INTO messages (id, guild, channel, author, content, date, indexed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    received.id,
                    received.guild.id,
                    received.channel.id,
                    received.author.id,
                    received.clean_content,
                    received.created_at,
                    indexed,
                ),
            )

        progress[str(message.channel.id)] = received.created_at
    con.commit()

    return count


def simple_tool(name, description) -> ChatCompletionToolParam:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {},
        },
    }


async def create_chat_completion(model: str, messages: list, tools: list):
    url = "http://localhost:8000/v1/mca/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ.get("HAGRID_SECRET"),
    }
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(payload)
        ) as response:
            return await response.json()


# noinspection SpellCheckingInspection
async def on_smart_message(message: Message):
    msg = message.clean_content.lower()

    # Basic commands
    if msg.startswith("/hagrid"):
        stat(message, "command")
        if msg == "/hagrid guild extend":
            settings[str(message.guild.id)] = True
            await message.delete()
        elif msg == "/hagrid channel index":
            set_index_status(message.channel.id, True)
            if hasattr(message.channel, "parent"):
                set_index_status(message.channel.parent.id, True)
            await message.delete()
        elif msg == "/hagrid channel noindex":
            set_index_status(message.channel.id, False)
            if hasattr(message.channel, "parent"):
                set_index_status(message.channel.parent.id, False)
            await message.delete()
        elif msg == "/hagrid scan":
            await message.delete()
            while await track(message) > 0:
                pass
        else:
            await message.channel.send(HAGRID_COMMANDS)

    # Track messages
    tracked = str(message.guild.id) in settings
    if tracked:
        await track(message)
    else:
        return

    # Summarize someones personality
    if "hagrid who is" in msg:
        await message.channel.typing()

        if len(message.mentions) == 0:
            await message.channel.send(f"Yer have to mention someone!")
        else:
            who = message.mentions[0].id
            description = await who_is(who)
            await message.channel.send(description)

        return True

    # Summarize a timespan
    if msg.startswith("hagrid what happened"):
        stat(message, "summary")

        await message.channel.typing()

        try:
            days_count = int(msg.split(" ")[-1])
        except ValueError:
            days_count = 1

        days_count = min(3, days_count)

        # Get the summary of the last n days
        here = msg.startswith("hagrid what happened here")
        summaries = [
            get_summary(message.guild.id, message.channel.id if here else -1, i)
            for i in range(days_count)
        ]
        summaries.reverse()

        msg = "Right then, 'ere's the summary:\n" + "\n\n".join(
            [
                f'**{to_date.strftime("%Y, %d %B")}:**\n{summary}'
                for (summary, from_date, to_date) in summaries
            ]
        )

        await message.channel.send(msg[:1500])

        return True

    convo_id = f"{message.author.id}_{message.channel.id}"

    if msg == "bye hagrid" and convo_id in active_conversations:
        del active_conversations[convo_id]
        return True

    if "hallo hagrid" in msg or (
        convo_id in active_conversations
        and (datetime.datetime.now() - active_conversations[convo_id]).seconds
        < MAX_CONVERSATION_TIME
    ):
        stat(message, "hallo hagrid")

        await message.channel.typing()

        active_conversations[convo_id] = datetime.datetime.now()

        # Use the last few messages from the channel as context
        messages = con.execute(
            """
            SELECT content, names.name as username
            FROM messages
            LEFT JOIN names ON names.id=messages.author
            WHERE channel=?
            ORDER BY date DESC 
            LIMIT ?
            """,
            (message.channel.id, MAX_HISTORY_N),
        ).fetchall()

        # Convert to OpenaAI messages
        messages = [
            {
                "role": "assistant" if "hagrid" in name.lower() else "user",
                "content": content.replace("\n", " "),
                "name": name.replace("HagridBot", "Hagrid"),
            }
            for content, name in messages
        ]

        messages.reverse()

        # System prompt and settings
        system_prompt = "You can use markdown formatting when required. Link the source of relevant phrases from the knowledge base when appopiate. You are in a Discord server dedicated to the Minecraft mod MCA (Minecraft Comes Alive)."
        messages.insert(
            0,
            {
                "role": "system",
                "content": f"[shared_memory:true][world_id:{message.guild.id}][character_id:hagrid]{system_prompt}",
            },
        )

        tools = []
        """
        if "hallo hagrid" not in msg:
            tools.append(
                simple_tool(
                    "quit",
                    "Stop the conversation, when the user is no longer talking to you.",
                )
            )

        tools.append(
            simple_tool(
                "paint",
                "Paint a beautiful picture based on the users request, if the user asks for a drawing.",
            )
        )
        """

        # noinspection PyBroadException
        try:
            response = await create_chat_completion("gpt-4o", messages, tools)
        except Exception:
            await message.channel.send(
                f"Blimey! Left the stove on, and now me hut's gone up in flames!"
            )
            return True

        # Process called tools
        response = response["choices"][0]["message"]
        for tool in response["tool_calls"]:
            if tool["function"]["name"] == "paint":
                await message.channel.send("Alright, give me a few seconds!")
                await asyncio.to_thread(
                    paint, message.content.replace("hallo hagrid", "").strip()
                )
                await message.channel.send(
                    "Here, I hope you like it!", file=File("image.webp")
                )
            elif tool["function"]["name"] == "quit":
                del active_conversations[convo_id]
                await message.add_reaction("👋")

        # Send the response
        if response["content"]:
            generated_text = response["content"].strip()
            await message.channel.send(generated_text)

        return True
