# Kling video for AstrBot

Generate one Kling V3 video in an AstrBot conversation through your own Ace Data Cloud account. `kling_generate_video` submits one text or first-frame video job; `kling_get_task` queries the same task until its final video is ready.

This independent **Kling integration is provided by Ace Data Cloud**; it is not an official plugin from the Kling publisher or the AstrBot team. Use your own Ace API key.

[简体中文指南](readme/README_zh_Hans.md) · [Kling Videos API](https://platform.acedata.cloud/documents/kling-videos?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=klingastrbot_readme_documents_kling_videos) · [Kling Tasks API](https://platform.acedata.cloud/documents/kling-tasks?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=klingastrbot_readme_documents_kling_tasks) · [Current prices](https://platform.acedata.cloud/services/kling?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=klingastrbot_readme_services_kling)

## 1. Find and install

Current upstream navigation is **Plugins → Plugins → Plugin Market / Installed**; older English versions may label the section Extensions. Search **Kling** and verify **Kling by Ace Data Cloud**, author **acedatacloud**, and the matching service icon.

**Publication status on 2026-10-19: not publicly listed in the official market.** The market search/install instructions above apply after publication. For the current preview, use the repository path below rather than waiting for a card that is not there.

Repository installation: **Plugins → Plugins → Installed → Install Plugin (+) → Install from URL**, with `https://github.com/AceDataCloud/KlingAstrBot`. Source is already available. Confirm it is enabled and loaded. A repository/file installation is a separate path from official market installation.

## Configure your key

New account? Register and sign in first. If the Applications page has no General application yet, choose **Initialize General Application**, then continue with the key steps below.

In [Ace Data Cloud Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=klingastrbot_readme_api_key), copy a generation API key from your General application or create a key that permits both `/kling/videos` and `/kling/tasks`. Check current per-second pricing, duration, and balance before submitting. Paste the key into the plugin's **Ace Data Cloud generation API key with Kling access** setting. Do not add `Bearer ` or use a `platform-...` management token. AstrBot masks the field in WebUI but stores the original value in its data directory, which should be protected.

Select a chat model that supports tool calling. Allow both Kling tools in the conversation's profile and persona.

### Token screenshots: copy or create a dedicated key

[Register or sign in to Ace](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=klingastrbot_readme_signup), then open **Applications → General application** and initialize it if absent. Use **1** to copy the selected key, or **2 Manage Keys → Create** for a dedicated key. If Allowed APIs is enabled, include `/kling/tasks` and `/kling/videos`; check current entitlement, balance and prices before use.

![Copy an Ace key or open Manage Keys (redacted)](_assets/tutorial/get-api-key-en.png)

Use a name such as `AstrBot Kling` and set expiry/limits as needed. The screenshot’s `Dify tutorial` is an older example, not a required label.

![Create an optional dedicated API key (shared Ace page, not AstrBot)](_assets/tutorial/create-api-key-en.png)

Images were reused and checked on **2026-10-19**; original capture dates are unknown. Credentials, App ID and balance are redacted. This is the shared Ace Applications UI, not proof of AstrBot installation or a live service call. [Image sources and limits](_assets/tutorial/sources.json).

### Where to paste it in AstrBot

Open **Plugins → Plugins → Installed**, select the gear (**Plugin Configuration**) on **Kling by Ace Data Cloud**, paste the key into **Ace Data Cloud generation API key with Kling access** (stored field `api_key`), and save. Paste the key only, with no `Bearer ` prefix; never put it in model-provider settings or a chat prompt. UI masking does not encrypt the data-directory config. These are exact text steps; no fabricated settings image is used.

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
