# Kling video for AstrBot

Generate one Kling V3 video in an AstrBot conversation through your own Ace Data Cloud account. `kling_generate_video` submits one text or first-frame video job; `kling_get_task` queries the same task until its final video is ready.

[简体中文指南](readme/README_zh_Hans.md) · [Kling Videos API](https://platform.acedata.cloud/documents/kling-videos) · [Kling Tasks API](https://platform.acedata.cloud/documents/kling-tasks) · [Current prices](https://platform.acedata.cloud/services/kling)

## Find and install

In AstrBot WebUI, open **Extensions → Plugins → AstrBot Plugin Market** and search **Kling**. Confirm the card says **Kling by Ace Data Cloud**, the author is **acedatacloud**, and the logo matches the [current Kling service icon](https://cdn.acedata.cloud/qpbbbb.jpg). Install it, then check **Installed** for load errors.

The official AstrBot Cloud listing is pending. After the source release is merged, **Installed → Install (+) → Install from URL** with `https://github.com/AceDataCloud/KlingAstrBot` can preview it. A URL installation does not prove market publication.

## Configure your key

In [Ace Data Cloud Applications](https://platform.acedata.cloud/console/applications), copy a generation API key from your General application or create a key that permits both `/kling/videos` and `/kling/tasks`. Check current per-second pricing, duration, and balance before submitting. Paste the key into the plugin's **Ace Data Cloud generation API key with Kling access** setting. Do not add `Bearer ` or use a `platform-...` management token. AstrBot masks the field in WebUI but stores the original value in its data directory, which should be protected.

Select a chat model that supports tool calling. Allow both Kling tools in the conversation's profile and persona.

## Generate once, then query

Ask the bot:

> Use `kling_generate_video` exactly once to make a yellow paper kite rising over a calm green meadow. Use 3 seconds and 16:9. Show me the task ID.

The tool sends one asynchronous `POST /kling/videos` request for `kling-v3` in `std` mode with `generate_audio: false`, then returns `status: submitted` with a task ID. Keep the ID and ask:

> Use `kling_get_task` with the exact task ID `<task_id>`. Tell me its status and final video URL. Do not generate another video.

If pending, query the same ID later. Kling's task item uses `state: succeed`; the plugin maps a finished task with a final HTTPS URL to `status: succeeded`. The plugin never retries a paid submission automatically.

The first version supports Kling V3 text-to-video and one authorized HTTPS `start_image_url`, with an optional `end_image_url` when a start frame is provided. Duration is 3–15 seconds; aspect ratio is `16:9`, `9:16`, or `1:1`. The plugin fixes standard mode and disables generated audio for predictable billing. Other Kling models, Omni references, video extension, motion, lip sync, and commercial actions are outside this version.

## Verify and troubleshoot

Match a returned trace ID in Ace Data Cloud usage when available. A finished task may include public `cost` amounts in Credits; confirm the live usage row before treating an estimate as a charge. Task lookup reads an existing job and does not submit another generation.

| Symptom | Check |
| --- | --- |
| Plugin fails to load | AstrBot version, **Failed to Load Plugins**, and **Data & Logs → Logs**. |
| Tools are missing | Plugin enabled, both tools allowed in the active profile and persona, chat model supports tool calling. |
| HTTP 401/403 | Key type, both allowed API paths, and account access. |
| Network error after submission | Inspect request history before generating again; a timeout may already have created a paid task. |
| Pending task | Query the same task ID later. |
| Failed task | Use the task or trace ID to inspect request history. |

The key goes only to `https://api.acedata.cloud`; redirects are rejected. The plugin exposes final video URLs and public cost fields to the model, without raw internal data. It uses Python's standard library and needs no runtime package installation.

## Validation and brand asset

On official AstrBot `v4.28.2`, an isolated editable installation registered both tools. ChatUI submitted one `kling-v3` 3-second standard silent video. The first task lookup exposed a distinct flat V3 terminal response, so the parser was fixed and the same task ID was queried again; no second generation was submitted. The final MP4 responded HTTP 200, `video/mp4`, and decoded as H.264, 1280×720, 3.042 seconds, with no audio track. The exact generation trace matched one successful `/kling/videos` usage row with 2.52 Credits original and 2.268 Credits deducted. See the [sanitized evidence](tests/e2e-results.json). First/end frames and other settings were validated structurally but not generated. This is a local editable installation; official Cloud review, market installation, and a first call from a market installation remain open.

`logo.png` is a PNG encoding of the unmodified 400×400 [current Kling service icon](https://cdn.acedata.cloud/qpbbbb.jpg). Source JPEG SHA-256: `f9c278baf15b5abb00d28c30cbf03d5ff4474798e49778b6ce2ee31bce92fe0f`; packaged PNG SHA-256: `d022899b0b98146a89fa0435f7382e02d142817ee2deb4dc53f33bbcbcbcbcb5`.
