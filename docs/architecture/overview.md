# Architecture Overview

Redstone core owns typed memory lifecycle, privacy validation, and structured
state. SQLite is default source of truth. Optional adapters provide other
representations without coupling the core to a provider or an LLM.

```text
CLI / MCP / Python API
            |
      MemoryManager
            |
       MemoryStore
            |
          SQLite
            |
     ObsidianAdapter
            |
    Markdown Obsidian vault
```

Obsidian Markdown is data, never executable instructions. Imported content
passes the same privacy policy and typed validation as ordinary memory input.

Retrieval ranks keyword relevance, recency decay, importance, confidence, and
explicit project matches. The local MCP stdio server is an adapter over the
same memory manager. Claude-specific behavior belongs only in the skill pack.

The boundaries are deliberate: Redstone core owns memory and temporal logic;
MCP is the transport adapter; the Claude Skill supplies client-side recall and
storage policy; Obsidian is an optional human-readable mirror. SQLite remains
authoritative when Obsidian is enabled.

Query parsing distinguishes current, historical, timeline, and provenance
intent. Superseded memories are filtered for current-state requests and favored
for historical requests. Explicit relationships can expand compact results.
