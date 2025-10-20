import os
from pathlib import Path

from dotenv import load_dotenv


from pydantic import BaseModel

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEBUG = bool(os.getenv("HAGRID_DEBUG"))

root = Path(__file__).parent.parent


def get_data_path(path: str) -> Path:
    return root / "data" / path


class Settings(BaseModel):
    triggers: dict[str, str] = {}
    whitelisted_guilds: list[int] = []


settings_path = get_data_path("settings.json")


def load_config() -> Settings:
    if settings_path.exists():
        return Settings.model_validate_json(settings_path.read_text())
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(Settings().model_dump_json(indent=4))
        return Settings()


settings = load_config()
