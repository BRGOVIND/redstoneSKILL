# Redstone

> **Your memories. Your vault. Your machine.**

Redstone is a local-first memory system for Claude and other AI assistants. It
stores useful facts, decisions, preferences, and project history on your own
machine, then recalls only what is relevant.

## Why I Built It

I saw a LinkedIn post from someone who built a personal memory system for his
AI workflow. It made me think about my own problem: every new Claude or AI
session forgot the decisions and context from earlier work.

I was tired of repeating myself and searching old conversations, so I started
building my own solution. That experiment became Redstone.

## What It Does

- Stores structured memories locally in SQLite
- Connects to Claude and other clients through MCP
- Provides an optional human-readable Obsidian mirror
- Tracks history, provenance, conflicts, and changed decisions
- Retrieves focused context instead of replaying every conversation
- Blocks obvious secrets and treats recalled memory as untrusted data
- Works offline without embeddings or a cloud database

## Architecture

```text
Claude / AI client
        |
   Skill + MCP
        |
     Redstone
     /      \
 SQLite   Obsidian
```

SQLite is the source of truth. Obsidian is an optional readable mirror. MCP
gives AI clients local memory tools, while the Skill guides Claude on when to
remember and recall information.

Redstone is built with Python 3.11+, SQLite, Pydantic, MCP, Pytest, and Ruff.

## Install

```bash
git clone https://github.com/BRGOVIND/redstoneSKILL.git
cd redstoneSKILL
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install .
```

Initialize and test:

```bash
redstone init
redstone doctor
redstone smoke-test
```

## Try It

```bash
redstone remember "Redstone uses SQLite" --project redstone
redstone search "storage" --project redstone
redstone recall "What storage did we choose?" --project redstone
```

## Connect an AI Client

Run the local MCP server:

```bash
redstone --root /path/to/workspace mcp
```

Build the Claude Skill:

```bash
redstone skill build
```

See the [MCP guide](docs/guides/mcp.md) and
[Claude validation guide](docs/guides/live-claude-validation.md) for setup.

## Optional Obsidian Vault

```bash
redstone obsidian init /path/to/Redstone-Vault
redstone obsidian export
redstone obsidian sync
```

## Status

Redstone v0.1.0 is alpha software. Its local core, MCP path, Skill packaging,
Obsidian synchronization, and deterministic tests work. Benchmarks are
synthetic or authored, and live Claude inference validation is still incomplete.

Redstone remains a personal project built for a simple goal: my Claude and my
other AIs should remember our work without taking ownership of that memory away
from me.

See [documentation](docs/README.md), [security policy](SECURITY.md), and
[contribution guide](CONTRIBUTING.md).

## License

[MIT](LICENSE)
