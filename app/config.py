import os
from pathlib import Path

from dotenv import load_dotenv


from pydantic import BaseModel, Field

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEBUG = bool(os.getenv("HAGRID_DEBUG"))

root = Path(__file__).parent.parent


def get_data_path(path: str) -> Path:
    return root / "data" / path


class Settings(BaseModel):
    class RankXpConfig(BaseModel):
        minute_bucket_decay_seconds: float = 60.0
        hour_bucket_decay_seconds: float = 3600.0
        base_xp_gain: float = 1.0
        minute_activity_weight: float = 8.0
        hour_activity_weight: float = 120.0
        min_xp_gain: int = 1
        max_xp_gain: int = 100

    triggers: dict[str, str] = Field(default_factory=dict)
    whitelisted_guilds: list[int] = Field(default_factory=list)
    rank_xp: RankXpConfig = Field(default_factory=RankXpConfig)


settings_path = get_data_path("settings.json")


def load_config() -> Settings:
    if settings_path.exists():
        return Settings.model_validate_json(settings_path.read_text())
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(Settings().model_dump_json(indent=4))
        return Settings()


settings = load_config()
