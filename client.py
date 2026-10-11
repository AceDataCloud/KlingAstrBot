"""Kling V3 video submission and existing-task lookup for AstrBot."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://api.acedata.cloud"
RATIOS = {"16:9", "9:16", "1:1"}
FAILED = {"failed", "error", "cancelled", "canceled", "rejected"}
SUCCEEDED = {"succeed", "succeeded"}


class _NoRedirect(HTTPRedirectHandler):
    """Never forward the configured key to another host."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(_NoRedirect)


class KlingError(RuntimeError):
    """An error safe to return to an AstrBot conversation."""


def _valid_https_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.netloc
        and not parsed.username
        and not parsed.password
    )


class KlingClient:
    """Submit one Kling V3 video or query an existing task."""

    def __init__(self, api_key: str) -> None:
        token = api_key.strip()
        if (
            not token
            or token.lower().startswith("bearer ")
            or token.startswith("platform-")
        ):
            raise KlingError(
                "Set an Ace Data Cloud generation API key in plugin settings."
            )
        self._api_key = token

    def _post(self, path: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        request = Request(
            API_BASE + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloudAstrBot/0.1.0",
            },
            method="POST",
        )
        try:
            with OPENER.open(request, timeout=90) as response:
                body = json.load(response)
                header_trace = response.headers.get(
                    "x-trace-id", ""
                ) or response.headers.get("x-request-id", "")
        except HTTPError as exc:
            raise KlingError(
                f"Ace Data Cloud returned HTTP {exc.code}. Check service access and request history."
            ) from None
        except (URLError, TimeoutError, OSError):
            raise KlingError(
                "The API connection failed. Check request history before submitting another video."
            ) from None
        except (ValueError, UnicodeError):
            raise KlingError(
                "The API returned invalid JSON. Check request history before retrying."
            ) from None
        if not isinstance(body, dict):
            raise KlingError("The API returned an unexpected response format.")
        return body, str(body.get("trace_id") or header_trace)

    async def submit(
        self,
        prompt: str,
        duration: int = 3,
        aspect_ratio: str = "16:9",
        start_image_url: str = "",
        end_image_url: str = "",
    ) -> dict[str, Any]:
        """Submit one asynchronous standard-mode Kling V3 video."""
        prompt = prompt.strip()
        if not prompt or len(prompt) > 4000:
            raise KlingError("Provide a video prompt of 1–4000 characters.")
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 3 <= duration <= 15
        ):
            raise KlingError("Duration must be 3–15 seconds.")
        if aspect_ratio not in RATIOS:
            raise KlingError("Choose a model-supported aspect ratio.")
        if start_image_url and not _valid_https_url(start_image_url):
            raise KlingError("Provide an authorized HTTPS first-frame image URL.")
        if end_image_url and (
            not start_image_url or not _valid_https_url(end_image_url)
        ):
            raise KlingError("An authorized HTTPS end frame requires a start frame.")
        payload: dict[str, Any] = {
            "action": "image2video" if start_image_url else "text2video",
            "model": "kling-v3",
            "prompt": prompt,
            "mode": "std",
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "generate_audio": False,
            "async": True,
        }
        if start_image_url:
            payload["start_image_url"] = start_image_url
        if end_image_url:
            payload["end_image_url"] = end_image_url
        body, trace_id = await asyncio.to_thread(self._post, "/kling/videos", payload)
        if body.get("success") is False or body.get("error"):
            raise KlingError(
                "Video submission was rejected. Check request history before trying again."
            )
        task_id = body.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise KlingError(
                "No task ID was returned. Check request history before submitting again."
            )
        return {
            "status": "submitted",
            "task_id": task_id,
            "trace_id": trace_id,
            "next_step": "Query this same task ID; do not submit another video while it is pending.",
        }

    async def query(self, task_id: str) -> dict[str, Any]:
        """Return the final video URL only after terminal task success."""
        task_id = task_id.strip()
        if not task_id or len(task_id) > 128:
            raise KlingError("Pass the exact task ID from Kling submission.")
        body, trace_id = await asyncio.to_thread(
            self._post, "/kling/tasks", {"id": task_id, "action": "retrieve"}
        )
        if body.get("success") is False or body.get("error"):
            raise KlingError("Task lookup failed. Check request history.")
        response = body.get("response")
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except ValueError:
                response = None
        if not isinstance(response, dict):
            response = {}
        data = response.get("data")
        items = data if isinstance(data, list) else []
        trace_id = str(response.get("trace_id") or body.get("trace_id") or trace_id)
        states = {
            str(item.get("state") or "").lower()
            for item in items
            if isinstance(item, dict)
        }
        if not items and ("state" in response or "video_url" in response):
            items = [response]
            states = {str(response.get("state") or "").lower()}
        if states & FAILED or response.get("success") is False or response.get("error"):
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "failed",
                "success": False,
                "video_urls": [],
            }
        if not body.get("finished_at") or response.get("success") is not True:
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "pending",
                "success": False,
                "video_urls": [],
            }
        urls = [
            item["video_url"]
            for item in items
            if isinstance(item, dict)
            and str(item.get("state") or "").lower() in SUCCEEDED
            and isinstance(item.get("video_url"), str)
            and _valid_https_url(item["video_url"])
        ]
        cost = response.get("cost")
        public_cost = (
            {
                key: cost[key]
                for key in ("amount", "list_amount", "currency")
                if key in cost
            }
            if isinstance(cost, dict)
            else {}
        )
        usage = response.get("usage")
        public_usage = (
            {"duration": usage["duration"]}
            if isinstance(usage, dict) and "duration" in usage
            else {}
        )
        if not public_usage and "duration" in response:
            public_usage = {"duration": response["duration"]}
        return {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "succeeded" if urls else "failed",
            "success": bool(urls),
            "video_urls": urls,
            "video_count": len(urls),
            "usage": public_usage,
            "cost": public_cost,
        }
