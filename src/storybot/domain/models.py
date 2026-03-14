from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


class SessionState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    WAITING_INPUT = "WAITING_INPUT"
    APPLYING_CHOICE = "APPLYING_CHOICE"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    STALE = "STALE"
    BROKEN = "BROKEN"


@dataclass(frozen=True)
class Choice:
    choice_id: str
    label: str
    target_node_ref: str
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Node:
    node_ref: str
    title: str
    body: str
    choices: tuple[Choice, ...] = ()
    ending_id: str | None = None


@dataclass(frozen=True)
class EngineAction:
    action_type: str
    choice_id: str | None = None


@dataclass(frozen=True)
class EngineStepResult:
    result_type: str
    node_ref: str
    title: str
    body: str
    available_choices: tuple[Choice, ...]
    is_terminal: bool
    ending_id: str | None
    state_patch: Mapping[str, str] = field(default_factory=dict)


@dataclass
class StorySession:
    session_id: str
    user_id: str
    campaign_id: str
    active_node_ref: str
    state: SessionState = SessionState.CREATED
    version: int = 0
    last_choice_id: str | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
