---
name: yt-transcript
description: Pull a YouTube video's transcript and do what the operator asks with it (summarize, extract points, answer questions), then keep answering follow-up questions about the video. Use when the operator runs /yt-transcript, or gives a YouTube link and asks to summarize it, get its transcript, or asks what a video says.
argument-hint: "[youtube url] <prompt>"
---

# /yt-transcript

Arguments: `$ARGUMENTS`

1. **Find the video.** Take the YouTube URL or 11-character video ID from the arguments. The rest of the arguments is the prompt. No URL in the arguments: use the most recent YouTube link in this conversation. None there: ask for one.
2. **Fetch.** Run `python -I <this skill>/scripts/fetch.py "<url>"` (`python3` on macOS / Linux). It needs `yt-dlp` with its `default` and `curl-cffi` extras on PATH, and Node.js (or Deno). When they are missing, tell the operator to install them (`uv tool install --python 3.12 "yt-dlp[default,curl-cffi]"`) and stop.
   - The script prints the transcript file path, title, caption track and word count. It picks English captions first, then the video's own language, and never a machine-translated track (YouTube rate-limits those with HTTP 429).
   - A non-English track: read it and answer in English.
   - The file starts with the video description. Use it to check the spelling of names and terms that auto-captions often get wrong.
   - "no usable captions": tell the operator and stop. Do not try other sources.
   - Errors that name sign-in, bot checks or HTTP 429: YouTube blocked the request. Report the error. A `yt-dlp` upgrade (`uv tool upgrade yt-dlp`) often fixes it. Do not retry in a loop, because repeated requests make the block worse.
3. **Read** the transcript file. Up to about 20,000 words, read the whole file. Above that, read it in parts, or grep it when the prompt asks about one topic.
4. **Answer the prompt.** No prompt: give a short summary (what the video covers, its main points, and any conclusion). Cite `[h:mm:ss]` timestamps for specific claims so the operator can jump to them. Use the timestamps in the file, which mark the start of a 30-second block.
5. **Follow-ups.** The transcript stays in context, so answer follow-up questions from it without fetching again. When a question is not covered in the video, say so instead of filling the gap from general knowledge.

## Limits

- Auto-generated captions have no punctuation or speaker labels, and they get names and technical terms wrong. Quote them with care and say when a quote comes from auto-captions with a likely error.
- The file holds only speech. It does not show what is on screen (slides, code, charts).
