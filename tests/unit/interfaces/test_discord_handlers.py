import pytest

from storybot.application.use_cases.story_runtime import StoryRuntime
from storybot.domain.engine import StoryEngine
from storybot.domain.models import Choice, Node
from storybot.domain.session_service import SessionService
from storybot.infrastructure.repositories.in_memory import (
    InMemoryContentRepository,
    InMemorySessionRepository,
)
from storybot.interfaces.discord.contracts import StartStoryCommand, StoryInteractionContext
from storybot.interfaces.discord.custom_id import ChoiceCustomIdPayload, CustomIdCodec
from storybot.interfaces.discord.handlers import InteractionRejectedError, StoryDiscordHandler


def make_handler() -> StoryDiscordHandler:
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
    service = SessionService(engine=engine, sessions=sessions)
    runtime = StoryRuntime(sessions=service, engine=engine)
    return StoryDiscordHandler(runtime=runtime, sessions=service, custom_ids=CustomIdCodec("secret"))


def test_start_returns_renderable_view_with_signed_choice() -> None:
    handler = make_handler()
    session_id, view = handler.handle_start(
        context=StoryInteractionContext(
            interaction_id="i1",
            user_id="u1",
            guild_id="g1",
            channel_id="c1",
        ),
        command=StartStoryCommand(campaign_id="main", entry_node_ref="main.ch1.start"),
    )

    assert session_id
    assert view.title == "Start"
    assert len(view.choices) == 1
    assert "|sig:" in view.choices[0].custom_id


def test_choice_from_other_user_is_rejected() -> None:
    handler = make_handler()
    session_id, _ = handler.handle_start(
        context=StoryInteractionContext(
            interaction_id="i1",
            user_id="owner",
            guild_id="g1",
            channel_id="c1",
        ),
        command=StartStoryCommand(campaign_id="main", entry_node_ref="main.ch1.start"),
    )

    encoded = handler.custom_ids.encode_choice(
        ChoiceCustomIdPayload(session_id=session_id, turn=0, choice_id="choice_left")
    )

    with pytest.raises(InteractionRejectedError):
        handler.handle_choice_custom_id(
            context=StoryInteractionContext(
                interaction_id="i2",
                user_id="intruder",
                guild_id="g1",
                channel_id="c1",
            ),
            custom_id=encoded,
        )


def test_stale_turn_custom_id_is_rejected() -> None:
    handler = make_handler()
    session_id, _ = handler.handle_start(
        context=StoryInteractionContext(
            interaction_id="i1",
            user_id="owner",
            guild_id="g1",
            channel_id="c1",
        ),
        command=StartStoryCommand(campaign_id="main", entry_node_ref="main.ch1.start"),
    )

    handler.handle_choice_custom_id(
        context=StoryInteractionContext(
            interaction_id="i2",
            user_id="owner",
            guild_id="g1",
            channel_id="c1",
        ),
        custom_id=handler.custom_ids.encode_choice(
            ChoiceCustomIdPayload(session_id=session_id, turn=0, choice_id="choice_left")
        ),
    )

    stale_custom_id = handler.custom_ids.encode_choice(
        ChoiceCustomIdPayload(session_id=session_id, turn=0, choice_id="choice_left")
    )
    with pytest.raises(InteractionRejectedError):
        handler.handle_choice_custom_id(
            context=StoryInteractionContext(
                interaction_id="i3",
                user_id="owner",
                guild_id="g1",
                channel_id="c1",
            ),
            custom_id=stale_custom_id,
        )
