# src/storybot/app/bootstrap.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from storybot.app.config import BotConfig
from storybot.application.use_cases.story_runtime import StoryRuntime
from storybot.domain.engine import StoryEngine
from storybot.domain.models import Node
from storybot.domain.session_service import SessionService
from storybot.infrastructure.repositories.in_memory import (
    InMemoryContentRepository,
    InMemorySessionRepository,
)
from storybot.interfaces.discord.custom_id import CustomIdCodec
from storybot.interfaces.discord.handlers import StoryDiscordHandler


@dataclass(slots=True)
class ApplicationContainer:
    config: BotConfig
    engine: StoryEngine
    session_service: SessionService
    runtime: StoryRuntime
    discord_handler: StoryDiscordHandler


def build_application(nodes: Mapping[str, Node]) -> ApplicationContainer:
    config = BotConfig.from_env()
    content_repo = InMemoryContentRepository(nodes=dict(nodes))
    session_repo = InMemorySessionRepository()
    engine = StoryEngine(content_repository=content_repo)
    session_service = SessionService(engine=engine, sessions=session_repo)
    runtime = StoryRuntime(sessions=session_service, engine=engine)
    custom_ids = CustomIdCodec(signing_secret=config.signing_secret)
    discord_handler = StoryDiscordHandler(runtime=runtime, sessions=session_service, custom_ids=custom_ids)
    return ApplicationContainer(
        config=config,
        engine=engine,
        session_service=session_service,
        runtime=runtime,
        discord_handler=discord_handler,
    )
