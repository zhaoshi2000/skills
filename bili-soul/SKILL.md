---
name: bili-soul
description: Run or extend the bundled BiliSoul app for Bilibili video subtitle and comment analysis, GUI monitoring, local comment drafts, and video mind-map notes. Use for BiliSoul workflows, not general Bilibili browsing.
---

# BiliSoul

The application lives in app/ beside this file. Run its commands with app/ as the working directory because configuration, the browser profile, downloads, and the database use relative paths. Read [app/README.md](app/README.md) for setup and current limitations.

## Analyze a video or the home feed

1. Create a virtual environment, install app/requirements.txt, and fill app/.env from app/.env.example with the user's own model endpoint and key. Keep credentials in local files only. Bilibili cookies, if needed, go into app/data/ as described in the app README.
2. For a visible Windows run, open app/启动图形界面.bat. The GUI supports start, pause/resume, stop, and close; pause and stop take effect after the current network, download, transcription, or model step.
3. For a single video, run from app/: .venv/Scripts/python.exe main.py run --url <BV-or-video-URL>. Run main.py run without a URL to sample the home feed. Use main.py queue to inspect local comment drafts.
4. The app tries existing subtitles first. If none are available, it downloads audio for remote SSH transcription when configured, then falls back to local speech recognition. Cite which source was used. Public comments are a limited hot-comment sample and do not represent all viewers.

Analysis and comment drafts remain local. Running the app does not authorize posting comments, likes, videos, dynamics, or notes.

## Make a mind-map note

When requested, use the sibling [video-mindmap-note skill](../video-mindmap-note/SKILL.md) to turn the time-coded subtitle into a concise outline and SVG/PNG diagram. Verify time anchors and attribute unverified claims to the speaker. Save a local draft before any Bilibili write.

For video-note APIs and their observed verification status, read [references/video-note-api.md](references/video-note-api.md). For broader read and interaction routes, read [references/api-catalog.md](references/api-catalog.md). The bundled app/video_note.py is a separate explicit note tool; check its help and the target video's current note state before using it. Distinguish private save, public submission, and approval. Do not publish unless the user requested it, and verify the resulting note by reading it back. A successful submit may still be awaiting Bilibili review.

Never package app/.env, app/data/, app/downloads/, browser profiles, logs, raw HAR files, or user media with this skill. The application is source code; the user's model key and Bilibili session are supplied locally after installation.
