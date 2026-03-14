from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class BotConfig:
    bot_token: str
    signing_secret: str
    startup_mode: str = "strict"
    default_campaign_id: str = "main"

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = getenv("STORYBOT_TOKEN", "")
        signing_secret = getenv("STORYBOT_SIGNING_SECRET", token or "dev-secret")
        startup_mode = getenv("STORYBOT_STARTUP_MODE", "strict")
        default_campaign_id = getenv("STORYBOT_DEFAULT_CAMPAIGN", "main")
        return cls(
            bot_token=token,
            signing_secret=signing_secret,
            startup_mode=startup_mode,
            default_campaign_id=default_campaign_id,
        )
