"""
Offline tests for peer_consult.swmidi — SWMIDI-8 wire format.

8 bytes little-endian: [status, pitch, velocity, error_mask, tick u32 @96 PPQ].
"""

import pytest

from casting_call import ModelAtlas

from peer_consult.swmidi import (
    EVENT_CAST,
    EVENT_CONSULT,
    EVENT_VERDICT,
    FRICTION_SEMANTIC,
    PPQ,
    STATUS_NOTE_ON,
    decode_event,
    encode_event,
    profile_channel,
)


class TestEncodeDecodeRoundTrip:
    def test_round_trip(self):
        blob = encode_event(STATUS_NOTE_ON, 10, EVENT_CONSULT, 96, FRICTION_SEMANTIC, 480)
        assert len(blob) == 8
        event = decode_event(blob)
        assert event == {
            "status_type": STATUS_NOTE_ON,
            "status": (STATUS_NOTE_ON << 4) | 10,
            "channel": 10,
            "pitch": EVENT_CONSULT,
            "velocity": 96,
            "error_mask": FRICTION_SEMANTIC,
            "tick": 480,
        }

    def test_byte_layout_little_endian(self):
        blob = encode_event(STATUS_NOTE_ON, 0x0D, 1, 127, FRICTION_SEMANTIC, 0x01020304)
        assert blob[0] == 0x0D          # status = NoteOn nibble 0x0 <<4 | channel
        assert blob[1] == 1             # pitch
        assert blob[2] == 127           # velocity
        assert blob[3] == 0b00000100    # error_mask
        assert blob[4:] == bytes([0x04, 0x03, 0x02, 0x01])  # tick u32 LE

    def test_event_type_constants(self):
        assert (EVENT_CAST, EVENT_CONSULT, EVENT_VERDICT) == (1, 2, 3)
        assert PPQ == 96
        # slackwater flux-core/src/swmidi.rs: EventType::NoteOn = 0.
        assert STATUS_NOTE_ON == 0x0
        # slackwater flux-core/src/error_mask.rs: SEMANTIC is bit 2.
        assert FRICTION_SEMANTIC == 0b0000_0100

    @pytest.mark.parametrize("kwargs", [
        {"status_type": 16},
        {"channel": 16},
        {"pitch": 128},
        {"velocity": -1},
        {"error_mask": 256},
        {"tick": -1},
    ])
    def test_out_of_range_rejected(self, kwargs):
        base = dict(status_type=0x9, channel=0, pitch=1, velocity=64, error_mask=0, tick=0)
        base.update(kwargs)
        with pytest.raises(ValueError):
            encode_event(**base)

    def test_decode_rejects_wrong_size(self):
        with pytest.raises(ValueError):
            decode_event(b"\x00" * 7)
        with pytest.raises(ValueError):
            decode_event(b"\x00" * 9)


class TestProfileChannel:
    def test_uses_atlas_channel_field(self):
        atlas = ModelAtlas.default()
        assert profile_channel(atlas.get("SEED_MINI")) == 10
        assert profile_channel(atlas.get("HERMES_405B")) == 13
        assert profile_channel(atlas.get("NEMOTRON_ULTRA")) == 14

    def test_none_channel_defaults_to_zero(self):
        atlas = ModelAtlas.default()
        assert atlas.get("GEMINI_PRO").channel is None
        assert profile_channel(atlas.get("GEMINI_PRO")) == 0
