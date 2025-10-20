import os
from typing import Optional, Union, List

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
)


async def generate_text(
    prompt: str,
    model: str = os.getenv("LLM_MODEL"),
    system_prompt: str = "You are Rubeus Hagrid, the loyal, friendly, and softhearted game assistant with a thick west country accent.",
    temperature: float = 0.7,
    max_tokens: int = 512,
    stop: Optional[Union[str, list]] = None,
) -> Union[List[str], str]:
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
