import pytest

from storybot.interfaces.discord.custom_id import ChoiceCustomIdPayload, CustomIdCodec, CustomIdError


def test_custom_id_round_trip() -> None:
    codec = CustomIdCodec(signing_secret="secret")
    encoded = codec.encode_choice(
        ChoiceCustomIdPayload(
            session_id="s1",
            turn=2,
            choice_id="choice_left",
        )
    )

    payload = codec.decode_choice(encoded)
    assert payload.session_id == "s1"
    assert payload.turn == 2
    assert payload.choice_id == "choice_left"


def test_custom_id_rejects_tampering() -> None:
    codec = CustomIdCodec(signing_secret="secret")
    encoded = codec.encode_choice(ChoiceCustomIdPayload(session_id="s1", turn=1, choice_id="c1"))
    tampered = encoded.replace("choice:c1", "choice:c2")

    with pytest.raises(CustomIdError):
        codec.decode_choice(tampered)


def test_custom_id_rejects_invalid_turn_value() -> None:
    codec = CustomIdCodec(signing_secret="secret")
    encoded = codec.encode_choice(ChoiceCustomIdPayload(session_id="s1", turn=1, choice_id="c1"))
    malformed = encoded.replace("turn:1", "turn:abc")

    with pytest.raises(CustomIdError):
        codec.decode_choice(malformed)
