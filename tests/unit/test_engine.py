# tests/unit/test_engine.py
import pytest

from storybot.domain.engine import EngineError, StoryEngine
from storybot.domain.models import Choice, EngineAction, Node
from storybot.infrastructure.repositories.in_memory import InMemoryContentRepository


def make_engine() -> StoryEngine:
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
    return StoryEngine(InMemoryContentRepository(nodes))


def test_apply_choice_transitions_to_target_node() -> None:
    engine = make_engine()
    result = engine.apply_action(
        node_ref="main.ch1.start",
        action=EngineAction(action_type="select_choice", choice_id="choice_left"),
    )

    assert result.node_ref == "main.ch1.left"
    assert result.is_terminal is True


def test_apply_choice_raises_for_invalid_choice() -> None:
    engine = make_engine()

    with pytest.raises(EngineError):
        engine.apply_action(
            node_ref="main.ch1.start",
            action=EngineAction(action_type="select_choice", choice_id="missing"),
        )
