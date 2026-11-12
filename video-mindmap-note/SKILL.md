---
name: video-mindmap-note
description: Turn time-coded video subtitles into a factual, timestamped study note and a shareable mind map. Use when a user asks for video notes, a video mind map, or both.
---

# Video mind map notes

Use the video's own subtitles when available; otherwise transcribe the audio. Keep a source link and the subtitle origin (creator-supplied, platform AI, or speech recognition). Do not treat subtitle errors as facts.

Read the full transcript before outlining. Build a short note with the thesis, 4–8 main ideas, supporting details, and useful time anchors. Preserve the speaker's uncertainty and distinguish claims from the speaker's evidence. Paraphrase rather than reproducing long stretches of the transcript. If a point is unclear, leave it out or mark it uncertain.

Create a JSON mind map with a root title and 4–8 branches. Each branch has a short label, an optional timestamp, and 2–5 compact points. Render it with:

    python scripts/render_mindmap.py outline.json mindmap.svg --png mindmap.png

The renderer uses only Python's standard library for SVG. PNG output needs Playwright and a local Chrome or Chromium browser. The JSON format is:

    {"title":"视频主题","subtitle":"根据视频字幕整理","branches":[{"label":"主要观点","timestamp":"03:20","points":["证据或解释","行动建议"]}]}

Review the image for clipped text and verify the note's time anchors against the subtitles. When putting the result into an external note editor, use the editor's supported rich text and image upload flow. Ask for the intended visibility if it matters and is unclear; saving a local draft does not imply permission to publish it.
