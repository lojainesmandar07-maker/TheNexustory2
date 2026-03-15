from __future__ import annotations

from typing import Protocol

from .models import Node, StorySession


class ContentRepository(Protocol):
    def get_node(self, node_ref: str) -> Node: ...


class SessionRepository(Protocol):
    def get_active_session(self, user_id: str, campaign_id: str) -> StorySession | None: ...

    def save(self, session: StorySession) -> StorySession: ...

    def get_by_id(self, session_id: str) -> StorySession | None: ...
