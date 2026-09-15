# Redstone Production Integration

## Readiness

**READY for local Claude/MCP integration.** The automated smoke test ran offline in a disposable workspace; it did not modify a user vault or production database.

## Architecture

Claude client + Skill -> local stdio MCP -> Redstone core -> SQLite. Obsidian is an optional human-readable mirror; SQLite remains authoritative.

## Installation and diagnostics

```bash
python -m pip install .
redstone init
redstone doctor
redstone smoke-test
redstone skill build
```

Runtime: Python 3.12. Package metadata requires Python 3.11+ and Pydantic 2.7+.

## MCP client configuration

```json
{
  "mcpServers": {
    "redstone": {
      "command": "redstone",
      "args": ["--root", "/path/to/workspace", "mcp"]
    }
  }
}
```

Verified lifecycle: `initialize`, `tools/list`, `memory_store`, `memory_recall`, and clean EOF shutdown.

## Obsidian workflow

```bash
redstone obsidian init /path/to/vault
redstone obsidian export
redstone obsidian sync
redstone obsidian status
```

The smoke test verified export/import round-trip equivalence using an isolated vault.

## Test results

```json
{
  "mcp": {
    "initialize": true,
    "recall": true,
    "store": true,
    "tools": 9
  },
  "memory": {
    "current": true,
    "historical": true,
    "provenance": true,
    "timeline_entries": 2
  },
  "obsidian": {
    "exported": 2,
    "imported": 2,
    "roundtrip": true
  },
  "offline": true,
  "security": {
    "secret_blocked": true,
    "untrusted_context": true
  },
  "skill": {
    "deterministic_package": true,
    "valid": true
  },
  "timings": {
    "initialization_ms": 6.3176000257954,
    "mcp_request_ms": 0.014199991710484028,
    "memory_write_ms": 8.359600033145398,
    "obsidian_sync_ms": 45.25130003457889,
    "recall_ms": 8.73840000713244,
    "temporal_composition_ms": 1.676499960012734
  }
}
```

## Limitations and known issues

Claude client registration and interactive client UI behavior remain external and were not automated. Obsidian needs a local writable vault. Real OpenAI evaluation remains optional and credential-driven. The clean-install verification used the built wheel with host Pydantic available; package build itself used an isolated PEP 517 environment. Core remains local-first with no mandatory embeddings, LLM consolidation, cloud storage, or UI.
