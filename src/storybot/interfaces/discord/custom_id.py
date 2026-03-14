from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


class CustomIdError(ValueError):
    pass


@dataclass(frozen=True)
class ChoiceCustomIdPayload:
    session_id: str
    turn: int
    choice_id: str


class CustomIdCodec:
    """Signed custom_id strategy: sb|v1|sid:<id>|turn:<n>|choice:<id>|sig:<hmac>."""

    VERSION = "v1"
    PREFIX = "sb"

    def __init__(self, signing_secret: str) -> None:
        self._secret = signing_secret.encode("utf-8")

    def encode_choice(self, payload: ChoiceCustomIdPayload) -> str:
        base = (
            f"{self.PREFIX}|{self.VERSION}|sid:{payload.session_id}|"
            f"turn:{payload.turn}|choice:{payload.choice_id}"
        )
        sig = self._signature(base)
        return f"{base}|sig:{sig}"

    def decode_choice(self, custom_id: str) -> ChoiceCustomIdPayload:
        parts = custom_id.split("|")
        if len(parts) != 6:
            raise CustomIdError("Malformed custom_id")

        prefix, version, sid_part, turn_part, choice_part, sig_part = parts
        if prefix != self.PREFIX or version != self.VERSION:
            raise CustomIdError("Unsupported custom_id version")

        if not sid_part.startswith("sid:") or not turn_part.startswith("turn:"):
            raise CustomIdError("custom_id missing routing fields")
        if not choice_part.startswith("choice:") or not sig_part.startswith("sig:"):
            raise CustomIdError("custom_id missing choice signature fields")

        base = "|".join(parts[:-1])
        supplied = sig_part.replace("sig:", "", 1)
        expected = self._signature(base)
        if not hmac.compare_digest(supplied, expected):
            raise CustomIdError("Invalid custom_id signature")

        turn = int(turn_part.replace("turn:", "", 1))
        return ChoiceCustomIdPayload(
            session_id=sid_part.replace("sid:", "", 1),
            turn=turn,
            choice_id=choice_part.replace("choice:", "", 1),
        )

    def _signature(self, data: str) -> str:
        return hmac.new(self._secret, data.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
