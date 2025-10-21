from discord import Message

from app.llm_utils import generate_text


async def get_last_messages(message: Message, limit: int = 10) -> list:
    messages = []
    async for received in message.channel.history(limit=limit):
        if received.clean_content:
            messages.append((received.author.name, received.clean_content))
    return messages


PROMPT = """
Given this discord conversation as context, which may be unrelated or outdated:
{conversation}

And the last message from a user:
{last_message}

Generate a response in the style of Hagrid. Try to be casual, you are not an assistant and can respond friendly, rude, sarcastically, or however you like.
Ignore the "Hey hagrid" prefixes, those are just to get your attention.
Respond in a single sentence.
"""


async def speak(message: Message):
    messages = await get_last_messages(message)
    messages.reverse()
    messages = [
        f"{author}: {content.replace('\n', ' ').strip()}"
        for author, content in messages
    ]

    return await generate_text(
        PROMPT.format(
            conversation="\n".join(messages[:-1]),
            last_message=messages[-1],
        )
    )
