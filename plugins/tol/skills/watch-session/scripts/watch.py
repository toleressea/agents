"""Follow a Claude Code session transcript and print one line per event worth a look.

python -I -u watch.py <transcript.jsonl> <out dir> [state.json]

Events: the session's chat (short status filler goes to <out dir>/filler.log),
agent dispatches and reports, questions, tool errors, operator messages, and
phase changes in an /orchestrate state.json.
"""
import json
import os
import sys
import time

transcript, out_dir = sys.argv[1], sys.argv[2]
state_path = sys.argv[3] if len(sys.argv) > 3 else None
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FILLER = ("still", "no report", "not reported", "waiting", "yet")


def emit(kind, msg, ts=""):
    print(f"{ts[11:16]} {kind}: " + " ".join(str(msg).split())[:400], flush=True)


def result_text(b):
    r = b.get("content")
    if isinstance(r, list):
        r = " ".join(x.get("text", "") for x in r if isinstance(x, dict))
    return r or ""


def phases():
    if not state_path:
        return None
    try:
        with open(state_path, encoding="utf-8") as f:
            return {i["id"]: i.get("phase") for i in json.load(f).get("items", [])}
    except (OSError, ValueError, KeyError):
        return None


def handle(e):
    ts = e.get("timestamp", "")
    content = (e.get("message") or {}).get("content")
    if e.get("type") == "user" and isinstance(content, str):
        if "[Subagent hand-back]" in content or content.startswith("Another Claude session"):
            end = content.find("</agent-message>")
            body = content[content.find("The report follows:") + 19:end if end > 0 else None]
            emit("AGENT REPORT", body, ts)
        elif not content.startswith("<"):
            emit("OPERATOR", content, ts)
        return
    for b in content if isinstance(content, list) else []:
        t = b.get("type")
        if e.get("type") == "assistant" and t == "text" and b["text"].strip():
            low = b["text"].lower()
            if len(low) < 200 and any(w in low for w in FILLER):
                with open(os.path.join(out_dir, "filler.log"), "a", encoding="utf-8") as f:
                    f.write(ts + " " + " ".join(b["text"].split()) + "\n")
            else:
                emit("SAYS", b["text"], ts)
        elif t == "tool_use" and b.get("name") in ("Agent", "AskUserQuestion", "Workflow"):
            inp = b.get("input", {})
            emit(b["name"], inp.get("description") or (inp.get("questions") or [{}])[0].get("question", ""), ts)
        elif t == "tool_result" and (b.get("is_error") or result_text(b).startswith("Exit code")):
            emit("TOOL ERROR", result_text(b)[:250], ts)


pos = os.path.getsize(transcript)
last = phases() or {}
buf = ""
while True:
    if os.path.getsize(transcript) > pos:
        with open(transcript, encoding="utf-8") as f:
            f.seek(pos)
            buf += f.read()
            pos = f.tell()
        *lines, buf = buf.split("\n")
        for line in lines:
            try:
                handle(json.loads(line))
            except (ValueError, KeyError, TypeError):
                continue
    now = phases()
    if now is not None and now != last:
        for k, v in now.items():
            if last.get(k) != v:
                emit("PHASE", f"{k} {last.get(k)} -> {v}")
        last = now
    time.sleep(3)
