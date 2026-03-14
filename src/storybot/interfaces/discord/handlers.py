from __future__ import annotations

from dataclasses import dataclass

from storybot.application.use_cases.story_runtime import StoryRuntime
from storybot.domain.models import EngineStepResult
from storybot.domain.session_service import SessionError, SessionService
from storybot.interfaces.discord.contracts import (
    ChooseStoryOptionCommand,
    ContinueStoryCommand,
    DiscordChoiceView,
    DiscordStoryView,
    StartStoryCommand,
    StoryInteractionContext,
)
from storybot.interfaces.discord.custom_id import ChoiceCustomIdPayload, CustomIdCodec, CustomIdError


class InteractionRejectedError(RuntimeError):
    """Raised when a Discord interaction cannot be accepted safely."""


@dataclass(slots=True)
class StoryDiscordHandler:
    runtime: StoryRuntime
    sessions: SessionService
    custom_ids: CustomIdCodec

    def handle_start(
        self,
        context: StoryInteractionContext,
        command: StartStoryCommand,
    ) -> tuple[str, DiscordStoryView]:
        session, result = self.runtime.start(
            user_id=context.user_id,
            campaign_id=command.campaign_id,
            entry_node_ref=command.entry_node_ref,
        )
        view = self._to_view(result=result, session_id=session.session_id, turn=session.version)
        return session.session_id, view

    def handle_continue(
        self,
        context: StoryInteractionContext,
        command: ContinueStoryCommand,
    ) -> DiscordStoryView:
        session = self._require_owned_session(context=context, session_id=command.session_id)
        latest, result = self.runtime.continue_active(session.session_id)
        return self._to_view(result=result, session_id=latest.session_id, turn=latest.version)

    def handle_choice(
        self,
        context: StoryInteractionContext,
        command: ChooseStoryOptionCommand,
    ) -> DiscordStoryView:
        session = self._require_owned_session(context=context, session_id=command.session_id)
        latest, result = self.runtime.choose(session.session_id, command.choice_id)
        return self._to_view(result=result, session_id=latest.session_id, turn=latest.version)

    def handle_choice_custom_id(self, context: StoryInteractionContext, custom_id: str) -> DiscordStoryView:
        try:
            payload = self.custom_ids.decode_choice(custom_id)
        except CustomIdError as exc:
            raise InteractionRejectedError("Invalid interaction payload") from exc

        session = self._require_owned_session(context=context, session_id=payload.session_id)
        if payload.turn != session.version:
            raise InteractionRejectedError("This choice is no longer valid. Use /story continue.")

        return self.handle_choice(
            context=context,
            command=ChooseStoryOptionCommand(session_id=payload.session_id, choice_id=payload.choice_id),
        )

    def _to_view(self, result: EngineStepResult, session_id: str, turn: int) -> DiscordStoryView:
        choices = tuple(
            DiscordChoiceView(
                label=choice.label,
                custom_id=self.custom_ids.encode_choice(
                    ChoiceCustomIdPayload(
                        session_id=session_id,
                        turn=turn,
                        choice_id=choice.choice_id,
                    )
                ),
            )
            for choice in result.available_choices
        )

        status_message = None
        if result.is_terminal:
            status_message = "Ending reached. Use /story restart to play again."

        return DiscordStoryView(
            title=result.title,
            body=result.body,
            choices=choices,
            is_terminal=result.is_terminal,
            status_message=status_message,
        )

    def _require_owned_session(self, context: StoryInteractionContext, session_id: str):
        try:
            session = self.sessions.get_session(session_id)
        except SessionError as exc:
            raise InteractionRejectedError("Session not found or unavailable.") from exc

        if context.user_id != session.user_id:
            raise InteractionRejectedError("Only the owning player can interact with this session.")
        return session
