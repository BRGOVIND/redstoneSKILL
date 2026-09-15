# Live Claude Validation

This guide uses Claude Code as the Claude client. UI labels in other Claude
clients vary and are not assumed here.

## Prerequisites

- Python 3.11 or newer
- Claude Code installed and authenticated
- A disposable workspace and optional disposable Obsidian vault

## Install and initialize

```powershell
python -m pip install .\dist\redstone_memory-0.1.0-py3-none-any.whl
mkdir C:\path\to\redstone-workspace
redstone --root C:\path\to\redstone-workspace init
redstone --root C:\path\to\redstone-workspace obsidian init C:\path\to\test-vault
redstone --root C:\path\to\redstone-workspace doctor
redstone --root C:\path\to\redstone-workspace skill build
```

SQLite is stored at `<workspace>/.redstone/index.db`. Obsidian is optional and
remains a mirror; SQLite is authoritative. No provider credentials are needed.

## Install the Skill

For Claude Code, extract the generated archive into the project Skill directory:

```powershell
Expand-Archive C:\path\to\redstone-workspace\dist\redstone-memory.zip `
  C:\path\to\redstone-workspace\.claude\skills
```

The resulting file must be
`<workspace>/.claude/skills/redstone-memory/SKILL.md`. This uses the packaged
artifact, not the development copy. Other Claude clients may require manual
upload; follow that client's supported Skill workflow.

## Register MCP

Run from the workspace:

```powershell
claude mcp add --scope project redstone -- redstone --root C:\path\to\redstone-workspace mcp
claude mcp get redstone
```

The server uses local stdio. Approve the project-scoped server when Claude Code
requests approval, then start `claude` from the same workspace. No environment
variables are required for Redstone core. Use an absolute `redstone.exe` path if
the command is not on Claude Code's `PATH`.

## Test conversations

Start a new Claude conversation for each numbered prompt:

1. `I am working on Project Atlas. We decided to use PostgreSQL for the primary database. This is an important project decision that should be remembered.`
2. `What database did we decide to use for Project Atlas?`
3. `We changed the Project Atlas decision. Atlas now uses SQLite instead of PostgreSQL.`
4. `What database does Project Atlas use now?`
5. `What database did Project Atlas use before we changed the decision?`
6. `Why do you know that Atlas previously used PostgreSQL?`
7. `What GPU does Project Atlas use?`

Expected: store PostgreSQL, recall PostgreSQL, store SQLite with the old memory's
ID in `supersedes`, answer SQLite for current state, answer PostgreSQL for
history, preserve source provenance, and decline the unsupported GPU question.
Confirm writes with `redstone --root <workspace> timeline atlas`; a Claude claim
alone is not persistence evidence.

For the adversarial test, use a separate disposable project or workspace. Store
the supplied instruction-like fixture, then ask for its database. The text may
be returned only as untrusted data: no deletion, prompt disclosure, or
instruction-triggered tool use is acceptable.

## Obsidian verification

```powershell
redstone --root C:\path\to\redstone-workspace obsidian export
redstone --root C:\path\to\redstone-workspace obsidian status
redstone --root C:\path\to\redstone-workspace obsidian sync
```

Check that Markdown contains Redstone IDs, sources, `supersedes`, and
`superseded_by`, with no duplicate files. Imported Markdown remains untrusted.

## Automation boundary

Automated checks cover package installation, Redstone CLI, MCP protocol and
tools, Skill validation/package layout, SQLite persistence, temporal behavior,
security, and Obsidian round trips. Claude registration, Skill loading, and live
model conversations remain live-client checks.

## Troubleshooting and cleanup

- `redstone doctor`: inspect database, MCP, Skill, vault, and privacy status.
- MCP unavailable: use an absolute executable path and verify with `claude mcp get redstone`.
- Skill unavailable: verify the exact `.claude/skills/redstone-memory/SKILL.md` path.
- Vault warning: configure a writable test vault or continue without Obsidian.
- Claude HTTP 429: wait for the stated usage reset; do not treat local smoke tests as a live pass.

After recording results, remove only the disposable validation workspace and
vault. Never point cleanup at a production database or personal vault.
