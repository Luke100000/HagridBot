import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

load_dotenv()


client = AsyncOpenAI(
    base_url=os.getenv("LLM_API_URL"),
    api_key=os.environ.get("LLM_API_KEY"),
    max_retries=10,
)


async def generate_text(
    prompt: str,
    model: str | None = None,
    system_prompt: str = "You are Rubeus Hagrid, the loyal, friendly, and softhearted game assistant with a thick west country accent.",
    temperature: float = 0.7,
    max_tokens: int = 512,
    stop: str | list | None = None,
) -> str | list[str]:
    if model is None:
        model = os.getenv("LLM_MODEL", "gpt-4o")

    messages = [
        ChatCompletionSystemMessageParam(content=system_prompt, role="system"),
        ChatCompletionUserMessageParam(content=prompt, role="user"),
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop,
    )

    return response.choices[0].message.content.strip()
