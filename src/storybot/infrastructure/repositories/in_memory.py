from __future__ import annotations

from copy import deepcopy

from storybot.domain.interfaces import ContentRepository, SessionRepository
from storybot.domain.models import Node, SessionState, StorySession


class InMemoryContentRepository(ContentRepository):
    def __init__(self, nodes: dict[str, Node]) -> None:
        self._nodes = nodes

    def get_node(self, node_ref: str) -> Node:
        node = self._nodes.get(node_ref)
        if node is None:
            raise KeyError(f"Missing node_ref '{node_ref}'")
        return node


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions_by_id: dict[str, StorySession] = {}

    def get_active_session(self, user_id: str, campaign_id: str) -> StorySession | None:
        for session in self._sessions_by_id.values():
            if (
                session.user_id == user_id
                and session.campaign_id == campaign_id
                and session.state
                not in (SessionState.CLOSED, SessionState.COMPLETED, SessionState.BROKEN)
            ):
                return deepcopy(session)
        return None

    def save(self, session: StorySession) -> StorySession:
        self._sessions_by_id[session.session_id] = deepcopy(session)
        return deepcopy(session)

    def get_by_id(self, session_id: str) -> StorySession | None:
        session = self._sessions_by_id.get(session_id)
        if session is None:
            return None
        return deepcopy(session)
