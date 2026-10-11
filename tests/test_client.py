"""Kling V3 request and terminal-result boundaries."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from client import KlingClient, KlingError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.headers = {"x-trace-id": "trace-kling"}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return json.dumps(self.payload).encode()


@pytest.mark.asyncio
async def test_submit_sends_one_async_silent_video_request():
    calls = []

    def fake_open(request, timeout):
        calls.append((request.full_url, json.loads(request.data), timeout))
        return FakeResponse({"task_id": "task-123"})

    with patch("client.OPENER.open", side_effect=fake_open):
        result = await KlingClient("test-key").submit("A paper kite rises")
    assert calls == [
        (
            "https://api.acedata.cloud/kling/videos",
            {
                "action": "text2video",
                "model": "kling-v3",
                "prompt": "A paper kite rises",
                "mode": "std",
                "duration": 3,
                "aspect_ratio": "16:9",
                "generate_audio": False,
                "async": True,
            },
            90,
        )
    ]
    assert result["status"] == "submitted"
    assert result["task_id"] == "task-123"
    assert "video_url" not in result


@pytest.mark.asyncio
async def test_image_request_uses_start_and_end_frames():
    with patch(
        "client.OPENER.open", return_value=FakeResponse({"task_id": "task-456"})
    ) as opening:
        await KlingClient("test-key").submit(
            "A kite rises",
            start_image_url="https://example.org/kite.png",
            end_image_url="https://example.org/sky.png",
        )
    payload = json.loads(opening.call_args.args[0].data)
    assert payload["action"] == "image2video"
    assert payload["start_image_url"] == "https://example.org/kite.png"
    assert payload["end_image_url"] == "https://example.org/sky.png"


@pytest.mark.asyncio
async def test_lookup_withholds_preview_and_internal_fields():
    pending = {"id": "task-123", "finished_at": None, "response": None}
    preview = {
        "finished_at": None,
        "response": {
            "success": True,
            "data": [
                {
                    "state": "succeed",
                    "video_url": "https://cdn.example.org/preview.mp4",
                }
            ],
        },
    }
    finished = {
        "finished_at": 123.0,
        "response": {
            "success": True,
            "data": [
                {
                    "state": "succeed",
                    "video_url": "https://cdn.example.org/final.mp4",
                    "supplier": "internal-only",
                }
            ],
            "cost": {
                "amount": 2.268,
                "list_amount": 2.52,
                "currency": "credit",
                "supplier": "internal-only",
            },
            "usage": {"duration": 3.04, "supplier": "internal-only"},
        },
    }
    failed = {
        "finished_at": 123.0,
        "response": {
            "success": False,
            "data": [
                {
                    "state": "failed",
                    "video_url": "https://cdn.example.org/preview.mp4",
                }
            ],
        },
    }
    with patch(
        "client.OPENER.open",
        side_effect=[
            FakeResponse(pending),
            FakeResponse(preview),
            FakeResponse(finished),
            FakeResponse(failed),
        ],
    ) as opening:
        first = await KlingClient("test-key").query("task-123")
        second = await KlingClient("test-key").query("task-123")
        last = await KlingClient("test-key").query("task-123")
        unsuccessful = await KlingClient("test-key").query("task-123")
    assert opening.call_count == 4
    assert first["status"] == second["status"] == "pending"
    assert first["video_urls"] == second["video_urls"] == []
    assert last["status"] == "succeeded"
    assert last["video_urls"] == ["https://cdn.example.org/final.mp4"]
    assert last["cost"] == {
        "amount": 2.268,
        "list_amount": 2.52,
        "currency": "credit",
    }
    assert last["usage"] == {"duration": 3.04}
    assert "supplier" not in str(last)
    assert unsuccessful["status"] == "failed"
    assert unsuccessful["video_urls"] == []


@pytest.mark.asyncio
async def test_query_accepts_flat_v3_terminal_response():
    finished = {
        "finished_at": 123.0,
        "response": {
            "success": True,
            "state": "succeed",
            "video_url": "https://cdn.example.org/v3.mp4",
            "duration": 3.041,
            "cost": {"amount": 2.268, "list_amount": 2.52, "currency": "credit"},
        },
    }
    with patch("client.OPENER.open", return_value=FakeResponse(finished)):
        result = await KlingClient("test-key").query("task-v3")
    assert result["status"] == "succeeded"
    assert result["video_urls"] == ["https://cdn.example.org/v3.mp4"]
    assert result["usage"] == {"duration": 3.041}


@pytest.mark.asyncio
async def test_invalid_inputs_never_submit_a_paid_job():
    client = KlingClient("test-key")
    for kwargs in (
        {"prompt": " "},
        {"prompt": "A kite", "duration": 2},
        {"prompt": "A kite", "aspect_ratio": "4:3"},
        {"prompt": "A kite", "start_image_url": "http://example.org/kite.png"},
        {"prompt": "A kite", "end_image_url": "https://example.org/sky.png"},
    ):
        with patch("client.OPENER.open") as opening, pytest.raises(KlingError):
            await client.submit(**kwargs)
        assert opening.call_count == 0
