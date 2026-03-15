# src/storybot/interfaces/discord/contracts.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoryInteractionContext:
    interaction_id: str
    user_id: str
    guild_id: str | None
    channel_id: str | None


@dataclass(frozen=True, slots=True)
class StartStoryCommand:
    campaign_id: str
    entry_node_ref: str


@dataclass(frozen=True, slots=True)
class ContinueStoryCommand:
    session_id: str


@dataclass(frozen=True, slots=True)
class ChooseStoryOptionCommand:
    session_id: str
    choice_id: str


@dataclass(frozen=True, slots=True)
class DiscordChoiceView:
    custom_id: str
    label: str


@dataclass(frozen=True, slots=True)
class DiscordStoryView:
    title: str
    body: str
    choices: tuple[DiscordChoiceView, ...]
    is_terminal: bool
    status_message: str | None = None
