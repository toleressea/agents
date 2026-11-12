# agents

Tol Eressea's Claude Code skills, commands, and global agent instructions.

## Install the plugin

```
/plugin marketplace add toleressea/agents
/plugin install tol@toleressea
```

Update later with `/plugin marketplace update toleressea`.

### Skills

| Skill | What it does |
|---|---|
| `/tol:pretty-html` | Dark-mode, self-contained HTML reports. Optional annotate mode, playable game-design sandbox, balance matrix. |
| `/tol:watch-session` | Watch another Claude Code session live, verify its claims, and collect findings on a live page. |
| `/tol:model-routing` | Weekly evidence-based refresh of which Claude model and effort to use for which work. Writes `~/.agents/model-routing.md`. |
| `/tol:claude-artifacts` | Work with Claude Docs artifacts from Zed or another ACP host. |
| `/tol:unity-cli` | Drive the running Unity Editor from the terminal through the Unity CLI. |
| `/tol:review` | Review a change through configurable lenses, verify each finding, and report. |
| `/tol:test` | Test a change through configurable stages: static, unit, integration, smoke, e2e. |
| `/tol:yt-transcript` | Pull a YouTube transcript with yt-dlp, answer a prompt about it, and take follow-up questions. Needs `yt-dlp[default,curl-cffi]` and Node.js. |
| `/tol:usage-loop` | Keep another skill or prompt running inside Claude plan usage caps: switch accounts, pause for a 5-hour reset, stop at the weekly cap. Needs `cswap`. |

### Commands

| Command | What it does |
|---|---|
| `/tol:temp-log-add [marker]` | Add temporary debug logs tagged with a marker. |
| `/tol:temp-log-remove [marker]` | Remove every log with that marker. |
| `/tol:normalize-audio <in> <out> [dB]` | Peak-normalize audio files with ffmpeg. |

## Configure composable skills

`tol:review` and `tol:test` are composable: each step (a review lens, a test stage) is bound to a skill or to plain instructions in a TOML config. The shipped `config.toml` next to each skill documents every key. Override it per user in `~/.agents/config/tol/<skill>.toml`, per repo in `.agents/config/tol/<skill>.toml`, or per run with `key=value` arguments:

```toml
# .agents/config/tol/review.toml
[lenses.simplicity]
skill = "ponytail:ponytail-review"
[lenses]
security = "off"
```

`/tol:review dry-run` prints the resolved config with the source of each key. A skill calling another tol skill needs the allow rule `Skill(tol:*)` outside auto mode. The convention is in [plugins/tol/conventions/composable.md](plugins/tol/conventions/composable.md).

## Global instructions

[global/CLAUDE.md](global/CLAUDE.md) is my global agent file. A plugin cannot install a CLAUDE.md, so on each device clone this repo and make `~/.claude/CLAUDE.md` one line:

```
@<path to clone>/global/CLAUDE.md
```

Then `git pull` updates it. The file imports `~/.agents/model-routing.md`. Run `/tol:model-routing` once on a new device to create that file.

## Develop

Load the working copy without installing: `claude --plugin-dir plugins/tol`.

🤖 Generated with stochastic optimism by clankers 🤖
