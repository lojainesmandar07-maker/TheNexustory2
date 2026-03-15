from __future__ import annotations

from dataclasses import dataclass

from storybot.domain.engine import StoryEngine
from storybot.domain.models import EngineStepResult, StorySession
from storybot.domain.session_service import SessionService


@dataclass
class StoryRuntime:
    """Application-level orchestrator for session flow and rendering data retrieval."""

    sessions: SessionService
    engine: StoryEngine

    def start(self, user_id: str, campaign_id: str, entry_node_ref: str) -> tuple[StorySession, EngineStepResult]:
        session = self.sessions.start_session(
            user_id=user_id,
            campaign_id=campaign_id,
            entry_node_ref=entry_node_ref,
        )
        result = self.engine.render_node(session.active_node_ref)
        return session, result

    def continue_active(self, session_id: str) -> tuple[StorySession, EngineStepResult]:
        session = self.sessions.continue_session(session_id)
        return session, self.engine.render_node(session.active_node_ref)

    def choose(self, session_id: str, choice_id: str) -> tuple[StorySession, EngineStepResult]:
        session = self.sessions.apply_choice(session_id=session_id, choice_id=choice_id)
        return session, self.engine.render_node(session.active_node_ref)
