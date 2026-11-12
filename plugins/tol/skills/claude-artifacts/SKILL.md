---
name: claude-artifacts
description: Use when the operator asks for an "artifact", a doc, or hands over a claude.ai/.../artifact/... link, especially in Zed or another ACP host. Artifacts are Claude Docs docs, made and edited with the claude_ai_Claude_Docs MCP tools.
---

# Claude artifacts from Zed / ACP

"Artifact" means a Claude Docs doc. Operate on it with the `mcp__claude_ai_Claude_Docs__*` tools, never a local file.

- **Load the tools.** `batch`, `guide`, `update` are usually listed. `read`, `query`, `create`, `delete` are deferred: load them with ToolSearch `select:<name>` first.
- **Load the rules.** If the Claude Docs server instructions are not in context, call `guide(items=["topic.instructions"])`. After a doc's birth, call `guide(items=["topic.index"])`. Follow the guide over this file.
- **No Artifact tool under ACP.** The adapter cannot render or open artifacts. After creating a doc, put its link in chat once. The operator views, edits and comments in a browser.
- **Read the operator's edits** with `read(ref=<body node>, engine="prose", payload={"kind":"view","sinceRev":<last rev>})`. List comments with `query(object="utterance", payload={"under":{"object":"node","id":"<body id>"}})`.
- **A claude.ai artifact link** is read with `read(ref={"object":"project","id":"<link>"})`, never web-fetched.

🤖 Generated with stochastic optimism by clankers 🤖
