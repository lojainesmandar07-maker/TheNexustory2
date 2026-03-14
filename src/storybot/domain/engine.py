from __future__ import annotations

from .interfaces import ContentRepository
from .models import Choice, EngineAction, EngineStepResult, Node


class EngineError(RuntimeError):
    pass


class StoryEngine:
    """Deterministic content-driven engine independent from Discord constructs."""

    def __init__(self, content_repository: ContentRepository) -> None:
        self._content = content_repository

    def render_node(self, node_ref: str) -> EngineStepResult:
        node = self._content.get_node(node_ref)
        return self._to_result(node)

    def apply_action(self, node_ref: str, action: EngineAction) -> EngineStepResult:
        current = self._content.get_node(node_ref)
        if action.action_type == "continue":
            return self._to_result(current)

        if action.action_type != "select_choice":
            raise EngineError(f"Unsupported action_type: {action.action_type}")

        if not action.choice_id:
            raise EngineError("choice_id is required for select_choice action")

        selected = self._find_choice(current.choices, action.choice_id)
        if selected is None:
            raise EngineError(f"choice_id '{action.choice_id}' is not valid for node '{node_ref}'")

        next_node = self._content.get_node(selected.target_node_ref)
        return self._to_result(next_node)

    @staticmethod
    def _find_choice(choices: tuple[Choice, ...], choice_id: str) -> Choice | None:
        for choice in choices:
            if choice.choice_id == choice_id:
                return choice
        return None

    @staticmethod
    def _to_result(node: Node) -> EngineStepResult:
        return EngineStepResult(
            result_type="ending" if node.ending_id else "render_node",
            node_ref=node.node_ref,
            title=node.title,
            body=node.body,
            available_choices=node.choices,
            is_terminal=node.ending_id is not None,
            ending_id=node.ending_id,
        )
