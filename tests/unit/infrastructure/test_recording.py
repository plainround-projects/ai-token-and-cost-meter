import json

import pytest

from tests.conftest import ScriptedModel
from token_meter.domain.errors import RecordingMissing
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore


def request(text="hi", tag="a"):
    return ChatRequest((ChatMessage.user(text),), max_output_tokens=10, tag=tag)


def test_recording_then_replaying_returns_the_same_response(tmp_path):
    path = tmp_path / "r.jsonl"
    live = ScriptedModel(lambda r: ("live answer", 12, 4))
    recorder = RecordingChatModel(live, RecordingStore(path), {"provider": "test"})
    first = recorder.complete(request())
    replay = RecordedChatModel(RecordingStore(path))
    assert replay.complete(request()) == first
    assert len(live.requests) == 1


def test_a_request_already_recorded_is_not_sent_again(tmp_path):
    live = ScriptedModel()
    recorder = RecordingChatModel(live, RecordingStore(tmp_path / "r.jsonl"), {})
    recorder.complete(request())
    recorder.complete(request())
    assert len(live.requests) == 1


def test_an_unrecorded_request_names_the_tag_and_the_fix(tmp_path):
    replay = RecordedChatModel(RecordingStore(tmp_path / "missing.jsonl"))
    with pytest.raises(RecordingMissing, match=r"tag='zzz'.*make record"):
        replay.complete(request(tag="zzz"))
    assert replay.name == "recorded"
    assert replay.supports_sampling


def test_the_note_about_what_produced_the_answer_is_kept_in_the_file(tmp_path):
    path = tmp_path / "r.jsonl"
    RecordingChatModel(ScriptedModel(), RecordingStore(path), {"provider": "test"}).complete(request())
    entry = json.loads(path.read_text().splitlines()[0])
    assert entry["recorded_with"] == {"provider": "test", "model": "scripted"}
    assert entry["tag"] == "a"


def test_a_folder_of_recordings_is_loaded_as_one_store(tmp_path):
    for name, text in (("one.jsonl", "q1"), ("two.jsonl", "q2")):
        RecordingChatModel(ScriptedModel(), RecordingStore(tmp_path / name), {}).complete(request(text))
    store = RecordingStore(tmp_path)
    assert len(store) == 2
    RecordedChatModel(store).complete(request("q1"))
    RecordedChatModel(store).complete(request("q2"))


def test_the_recorder_reports_the_wrapped_models_name_and_sampling_support(tmp_path):
    recorder = RecordingChatModel(ScriptedModel(sampling=False), RecordingStore(tmp_path / "r.jsonl"), {})
    assert recorder.name == "scripted"
    assert not recorder.supports_sampling
