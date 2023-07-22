import os
from functools import lru_cache
from typing import Optional, Union, List

import numpy as np
import openai as openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


@lru_cache(256)
def generate_embedding(text: str) -> np.array:
    text = text.replace("\n", " ")
    return np.asarray(
        openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][
            0
        ]["embedding"],
        dtype=np.float32,
    )


def generate_text(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.5,
    max_tokens: int = 256,
    n: int = 1,
    stop: Optional[Union[str, list]] = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0.1,
) -> Union[List[str], str]:
    """
    chat_generate_text - Generates text using the OpenAI API.
    :param str prompt: prompt for the model
    :param str model: model to use, defaults to "gpt-3.5-turbo"
    :param str system_prompt: initial prompt for the model, defaults to "You are a helpful assistant."
    :param float temperature: _description_, defaults to 0.5
    :param int max_tokens: _description_, defaults to 256
    :param int n: _description_, defaults to 1
    :param Optional[Union[str, list]] stop: _description_, defaults to None
    :param float presence_penalty: _description_, defaults to 0
    :param float frequency_penalty: _description_, defaults to 0.1
    :return List[str]: _description_
    """
    messages = [
        {"role": "system", "content": f"{system_prompt}"},
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        n=n,
        stop=stop,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )

    generated_texts = [
        choice.message["content"].strip() for choice in response["choices"]
    ]
    return generated_texts[0] if n == 1 else generated_texts
