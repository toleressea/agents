---
name: pretty-html
description: Make a dark-mode, self-contained HTML report about whatever the operator names (findings, a comparison, research, a run summary, a design walkthrough), and open it in Chrome. Optional annotate mode lets the operator attach notes to any block and export them back, a report can carry a playable sandbox for trying and tuning game designs by feel, and a balance matrix compares many things on shared numbers with sliders whose changes export back. Use when the operator runs /pretty-html or asks for a "pretty HTML report", "dark mode page" or "HTML summary", or wants to try, fly, play or tune a game design in the browser before writing code, or to compare and rebalance the stats of many enemies, weapons or items.
argument-hint: "<what the report is about> [annotate] [no-open]"
---

# /pretty-html

One HTML file the operator can read at a glance and keep. The topic comes from `$ARGUMENTS`.

## Content

- Gather the facts first, from code, files, transcripts, commands or the web, as the topic needs. Every number, quote and claim on the page comes from something you read or ran. Name the source next to it (a file path, a command, a URL). If a fact can't be checked, say so on the page.
- Lead with the answer: a one-line lede, then the most important part. Detail goes lower, or into `<details>`.
- Organize by what the reader decides or checks, not by the order you found things.
- Follow the operator's writing rules (CLAUDE.md) in every line.
- For a chart, load the `dataviz` skill first.

## Build

- Start from `${CLAUDE_SKILL_DIR}/assets/base.html`: replace `__TITLE__` and `__LEDE__`, and write the body with its classes (`card`, `grid` + `stat`, `table`, `tag ok|bad|warn`, `callout info|bad|ok`, `nav.toc`). Add CSS only for what the base lacks.
- HTML-escape `&`, `<`, `>` and `"` in all quoted or gathered text (logs, transcript lines, code) before you insert it. Put code in `<pre><code>` after escaping.
- One file, no external requests: inline styles and scripts, embed small images as data URIs.
- Keep the footer line.
- Save to `~/.agents/reports/<slug>.html`, unless the operator names another place. An existing file with that name is overwritten only when it is this report's earlier version.

## Annotate mode

When `$ARGUMENTS` contains `annotate`, paste `${CLAUDE_SKILL_DIR}/assets/annotate.js` into a `<script>` at the end of `<body>`. Each heading, paragraph, list item, table row, code block, stat and callout then gets a "+" on hover. A note is kept in the browser (`localStorage`), so it survives a reload. **Export** downloads `<slug>.notes.json` and copies the notes as Markdown.

Tell the operator: write notes, press Export, and say so. Then read the newest `~/Downloads/<slug>.notes*.json`. Each note carries the excerpt of the block it belongs to.

## Playable sandbox

When the operator wants to try designs by feel (fly, drive, jump, tune while playing), the report gets a canvas sandbox. Build it from `${CLAUDE_SKILL_DIR}/assets/sandbox.js` (fixed-step loop, keyboard and mouse, full screen, slider rows, saved tuning with JSON export, seeded random, headless self-test).

The sandbox has:

1. **The game's own rules, read from the code**, with each source listed on the page: step rate, mass and force units, damping, turning, collisions, camera framing. Say which parts are not simulated.
2. **"In game now" reference presets** next to the proposals, and a callout asking the operator to check the sandbox against the game before trusting it.
3. **Live tuning**: sliders that change the running simulation, saved in `localStorage`, plus **Export JSON** for the values to go into the game.
4. **Something to do**: obstacles, threats and a scored run (lap time, hits), so designs compare by result as well as feel. Seed any generated layout.
5. **A comparison** (table, chart) computed from the same live values.
6. **A camera like the game's**, and a Full screen button for a 1:1 feel.

Before handing it over: `node --check` the extracted script, run the `#selftest` hook headless and compare its numbers with the hand-computed ones, and screenshot the page headless (`--screenshot`) to check the layout. Give every element a unique `id`: `getElementById` returns the first match.

## Balance matrix

When the operator wants to compare or tune many things on shared numbers (enemies, weapons, items), build from `${CLAUDE_SKILL_DIR}/assets/balance-matrix.html` instead of the base. Each row is a thing and each column a shared stat. Every bar is scaled to its column's maximum and coloured on a blue-to-yellow ramp. With **Edit** on, each cell becomes a slider: the bars rescale live, formula columns recompute, and **Export** downloads `<slug>-changes.json`, listing each changed source field with its from and to values. The data contract is in the comment at the top of the file.

- Read the values from the live source of truth (for Unity, the open Editor through `unity command eval`), not by parsing asset files.
- Tie every slider to a real field. Use `toField` when the column shows something else (a cooldown shown as a rate is `1 / x`), and a `formula` column for anything computed from several fields (damage per second). A cell without `field` is shown with no slider.
- Then read the newest `~/Downloads/<slug>-changes*.json`, apply it, read the source back and compare every field with the export before reporting it done. Run the project's tests too: a balance pass breaks tests that assert tuned values.

## Open

Unless `$ARGUMENTS` contains `no-open`, open it in Chrome. On Windows: `Start-Process chrome '<file>'`, or with the full path `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` if `chrome` does not resolve. On macOS: `open -a "Google Chrome" '<file>' || open '<file>'`. On Linux: `google-chrome '<file>'`, or `xdg-open '<file>'` for the default browser. Give the operator the path as a `file:///` URL too.

🤖 Generated with stochastic optimism by clankers 🤖
