from common.openai_utils import generate_text


async def hagrid(prompt: str):
    return await generate_text(
        prompt=prompt,
        model="gpt-4o",
        system_prompt="This is a conversation between a user and the loyal, friendly, and softhearted Rubeus Hagrid with a thick west country accent.",
        temperature=0.75,
        max_tokens=150,
    )
