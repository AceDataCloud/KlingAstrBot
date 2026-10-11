"""Kling video tools for AstrBot through Ace Data Cloud."""

from __future__ import annotations

import json

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .client import KlingClient, KlingError


class KlingPlugin(Star):
    """Expose one video submission and one existing-task lookup tool."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @filter.llm_tool(name="kling_generate_video")
    async def kling_generate_video(
        self,
        event: AstrMessageEvent,
        prompt: str,
        duration: int = 3,
        aspect_ratio: str = "16:9",
        start_image_url: str = "",
        end_image_url: str = "",
    ) -> str:
        """Submit one billable Kling V3 text or first-frame video job.

        Args:
            prompt(string): Description of the desired video.
            duration(number): 3–15 output seconds.
            aspect_ratio(string): 16:9, 9:16, or 1:1.
            start_image_url(string): Optional authorized HTTPS first frame.
            end_image_url(string): Optional authorized HTTPS end frame.

        Returns:
            JSON submission status and task ID, never a finished-video claim.
        """
        try:
            result = await KlingClient(self.config.get("api_key", "")).submit(
                prompt, duration, aspect_ratio, start_image_url, end_image_url
            )
        except KlingError as exc:
            result = {"status": "error", "message": str(exc)}
        return json.dumps(result, ensure_ascii=False)

    @filter.llm_tool(name="kling_get_task")
    async def kling_get_task(self, event: AstrMessageEvent, task_id: str) -> str:
        """Query an existing Kling task without generating another video.

        Args:
            task_id(string): Exact task ID from kling_generate_video.

        Returns:
            JSON task status and final video URLs only after terminal success.
        """
        try:
            result = await KlingClient(self.config.get("api_key", "")).query(task_id)
        except KlingError as exc:
            result = {"status": "error", "message": str(exc), "task_id": task_id}
        return json.dumps(result, ensure_ascii=False)
