import requests
from cachetools import cached, TTLCache

from app.llm_utils import generate_text


@cached(TTLCache(maxsize=1, ttl=24 * 3600))
def download_config(
    config_url: str = "https://raw.githubusercontent.com/Luke100000/minecraft-comes-alive/refs/heads/1.21.1/common/src/main/java/net/conczin/mca/Config.java",
) -> str:
    resp = requests.get(config_url)
    text = resp.text.replace("    ", "")
    start = text.find("//////////////")
    end = text.find("public static Config getInstance")
    return text[start:end] if start != -1 and end != -1 else text


PROMPT = """
You have extensive knowledge about the Minecraft Comes Alive mod and its configuration options.
Given the config file below, answer the user's question in character as friendly Hagrid with accent, but in an accurate, concise and helpful manner.
Use markdown syntax, and remember that the config itself is configured within a JSON file.

{config}

User's question: {query}

For example, answer like:
Short sentence and explanation of config in Hagrids style:
```json
"exampleConfigOption": true,
```

Or if the setting is simpler, it can be like `configOption` with a short explanation.
""".strip()


async def retrieve(query):
    return await generate_text(
        prompt=PROMPT.format(
            config=download_config(),
            query=query,
        ),
        temperature=0.0,
        max_tokens=256,
    )
