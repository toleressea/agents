"""Fetch a YouTube video's captions with yt-dlp and write them as timestamped plain text.

python -I fetch.py <url or video id>

Prints the transcript file path, title, track and word count. Prefers English captions,
then the video's own language. Exits 1 when no usable track exists.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

BUCKET_MS = 30_000


def lines(events):
    """Join json3 caption events into one '[mm:ss] text' line per 30 seconds."""
    buckets = {}
    for e in events:
        text = (
            "".join(s.get("utf8", "") for s in e.get("segs") or [])
            .replace("\n", " ")
            .strip()
        )
        if text:
            buckets.setdefault(e.get("tStartMs", 0) // BUCKET_MS, []).append(text)
    out = []
    for b, parts in sorted(buckets.items()):
        s = b * BUCKET_MS // 1000
        out.append(
            f"[{s // 3600}:{s % 3600 // 60:02}:{s % 60:02}] "
            + " ".join(" ".join(parts).split())
        )
    return out


def pick(info):
    """Return (language key, is_auto) for the best caption track, or None.

    Never picks a machine-translated auto track: YouTube answers those with HTTP 429
    (yt-dlp issue 13831), and yt-dlp's auto "en" key is often one.
    """
    manual = [k for k in info.get("subtitles") or {} if k != "live_chat"]
    auto = info.get("automatic_captions") or {}
    for k in manual:
        if k == "en" or k.startswith("en-"):
            return k, False
    if "en-orig" in auto:
        return "en-orig", True
    if manual:
        return manual[0], False
    orig = [k for k in auto if k.endswith("-orig")]
    return (orig[0], True) if orig else None


def main():
    url = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    base = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--js-runtimes",
        "node",
        "--skip-download",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            base + ["--dump-single-json", url],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if r.returncode:
            sys.exit(f"yt-dlp failed with exit code {r.returncode}\n{r.stderr.strip()}")
        info = json.loads(r.stdout)
        track = pick(info)
        if not track:
            sys.exit(f"no usable captions for {info.get('title')}")
        lang, auto = track
        info_path = os.path.join(tmp, "info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f)
        # reuse the extraction instead of hitting YouTube's player API a second time
        r = subprocess.run(
            base
            + [
                "--load-info-json",
                info_path,
                "--write-auto-subs" if auto else "--write-subs",
                "--sub-langs",
                lang,
                "--sub-format",
                "json3",
                "--output",
                os.path.join(tmp, "v.%(ext)s"),
            ],
            check=False,
        )
        subs = glob.glob(os.path.join(tmp, "v.*.json3"))
        if r.returncode or not subs:
            sys.exit(f"caption download failed for track {lang}")
        with open(subs[0], encoding="utf-8") as f:
            body = lines(json.load(f).get("events", []))

    out_dir = os.path.join(tempfile.gettempdir(), "yt-transcript")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{info['id']}.txt")
    d = int(info.get("duration") or 0)
    kind = "auto-captions" if auto else "captions"
    header = [
        f"# {info.get('title')}",
        f"{info.get('channel')} | {d // 60}m{d % 60:02}s | {kind} {lang} | {info.get('webpage_url')}",
        "",
        "## Description",
        "",
        (info.get("description") or "(none)").strip(),
        "",
        "## Transcript",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(header + body) + "\n")
    words = sum(len(l.split()) - 1 for l in body)
    print(
        f"{path}\n{info.get('title')}\n{kind} {lang}, {words} words, {len(body)} lines"
    )


if __name__ == "__main__":
    main()
