from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .engine import EngineError, StoryEngine
from .interfaces import SessionRepository
from .models import EngineAction, SessionState, StorySession


class SessionError(RuntimeError):
    """Raised for invalid session lifecycle operations."""


class SessionService:
    def __init__(self, engine: StoryEngine, sessions: SessionRepository) -> None:
        self._engine = engine
        self._sessions = sessions

    def start_session(self, user_id: str, campaign_id: str, entry_node_ref: str) -> StorySession:
        existing = self._sessions.get_active_session(user_id=user_id, campaign_id=campaign_id)
        if existing and existing.state not in (SessionState.COMPLETED, SessionState.CLOSED):
            return existing

        session = StorySession(
            session_id=str(uuid4()),
            user_id=user_id,
            campaign_id=campaign_id,
            active_node_ref=entry_node_ref,
            state=SessionState.WAITING_INPUT,
        )
        return self._sessions.save(session)

    def continue_session(self, session_id: str) -> StorySession:
        session = self._require_session(session_id)
        if session.state in (SessionState.CLOSED, SessionState.BROKEN):
            raise SessionError(f"Session {session_id} is not resumable: {session.state}")

        result = self._engine.render_node(session.active_node_ref)
        session.state = SessionState.COMPLETED if result.is_terminal else SessionState.WAITING_INPUT
        session.updated_at = datetime.now(tz=timezone.utc)
        session.version += 1
        return self._sessions.save(session)

    def apply_choice(self, session_id: str, choice_id: str) -> StorySession:
        session = self._require_session(session_id)
        if session.state != SessionState.WAITING_INPUT:
            raise SessionError(
                f"Session {session_id} cannot accept choices in state {session.state}. Expected WAITING_INPUT."
            )

        session.state = SessionState.APPLYING_CHOICE
        session.updated_at = datetime.now(tz=timezone.utc)
        session.version += 1
        self._sessions.save(session)

        try:
            result = self._engine.apply_action(
                node_ref=session.active_node_ref,
                action=EngineAction(action_type="select_choice", choice_id=choice_id),
            )
        except EngineError as exc:
            # Return session to interactive state when a choice payload is invalid.
            session.state = SessionState.WAITING_INPUT
            session.updated_at = datetime.now(tz=timezone.utc)
            session.version += 1
            self._sessions.save(session)
            raise SessionError(str(exc)) from exc
        except Exception as exc:  # unexpected runtime issues should mark the session as broken.
            session.state = SessionState.BROKEN
            session.updated_at = datetime.now(tz=timezone.utc)
            session.version += 1
            self._sessions.save(session)
            raise SessionError(f"Session {session_id} entered BROKEN state due to runtime failure") from exc

        session.active_node_ref = result.node_ref
        session.last_choice_id = choice_id
        session.state = SessionState.COMPLETED if result.is_terminal else SessionState.WAITING_INPUT
        session.updated_at = datetime.now(tz=timezone.utc)
        session.version += 1
        return self._sessions.save(session)

    def get_session(self, session_id: str) -> StorySession:
        return self._require_session(session_id)

    def close_session(self, session_id: str) -> StorySession:
        session = self._require_session(session_id)
        session.state = SessionState.CLOSED
        session.updated_at = datetime.now(tz=timezone.utc)
        session.version += 1
        return self._sessions.save(session)

    def _require_session(self, session_id: str) -> StorySession:
        session = self._sessions.get_by_id(session_id)
        if session is None:
            raise SessionError(f"Session {session_id} was not found")
        return session
