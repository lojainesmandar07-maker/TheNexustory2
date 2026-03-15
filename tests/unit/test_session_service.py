# tests/unit/test_session_service.py
import pytest

from storybot.domain.engine import StoryEngine
from storybot.domain.models import Choice, Node, SessionState
from storybot.domain.session_service import SessionError, SessionService
from storybot.infrastructure.repositories.in_memory import (
    InMemoryContentRepository,
    InMemorySessionRepository,
)


def make_service() -> SessionService:
    nodes = {
        "main.ch1.start": Node(
            node_ref="main.ch1.start",
            title="Start",
            body="Start body",
            choices=(Choice(choice_id="choice_left", label="Left", target_node_ref="main.ch1.left"),),
        ),
        "main.ch1.left": Node(
            node_ref="main.ch1.left",
            title="Left",
            body="Left body",
            ending_id="ending_left",
        ),
    }
    engine = StoryEngine(InMemoryContentRepository(nodes))
    sessions = InMemorySessionRepository()
    return SessionService(engine=engine, sessions=sessions)


def test_start_then_apply_choice_completes_session() -> None:
    service = make_service()
    started = service.start_session(user_id="u1", campaign_id="main", entry_node_ref="main.ch1.start")
    updated = service.apply_choice(session_id=started.session_id, choice_id="choice_left")

    assert updated.active_node_ref == "main.ch1.left"
    assert updated.state == SessionState.COMPLETED
    assert updated.last_choice_id == "choice_left"


def test_apply_choice_raises_for_missing_session() -> None:
    service = make_service()

    with pytest.raises(SessionError):
        service.apply_choice(session_id="does-not-exist", choice_id="choice_left")


def test_apply_choice_rejects_when_not_waiting_for_input() -> None:
    service = make_service()
    started = service.start_session(user_id="u1", campaign_id="main", entry_node_ref="main.ch1.start")
    service.close_session(started.session_id)

    with pytest.raises(SessionError):
        service.apply_choice(session_id=started.session_id, choice_id="choice_left")
