from __future__ import annotations

from dataclasses import dataclass

from storybot.app.config import BotConfig
from storybot.domain.engine import StoryEngine
from storybot.domain.session_service import SessionService
from storybot.infrastructure.repositories.in_memory import (
    InMemoryContentRepository,
    InMemorySessionRepository,
)


@dataclass
class ApplicationContainer:
    config: BotConfig
    session_service: SessionService


def build_application(nodes: dict) -> ApplicationContainer:
    config = BotConfig.from_env()
    content_repo = InMemoryContentRepository(nodes=nodes)
    session_repo = InMemorySessionRepository()
    engine = StoryEngine(content_repository=content_repo)
    service = SessionService(engine=engine, sessions=session_repo)
    return ApplicationContainer(config=config, session_service=service)
