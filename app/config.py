import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WHITELISTED_GUILDS = [
    747184859386085380,
    1008386913889177710,
    697239211237179414,
    890529813020938280,
    1246536983728230601,
]


TOKEN = os.getenv("DISCORD_TOKEN")
DEBUG = bool(os.getenv("HAGRID_DEBUG"))

root = Path(__file__).parent.parent


def get_data_path(path: str) -> Path:
    return root / "data" / path