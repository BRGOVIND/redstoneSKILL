# MCP

Redstone exposes local stdio JSON-RPC MCP transport:

```bash
redstone --root /path/to/workspace mcp
```

Example client configuration:

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

The server is local-only. Returned memory remains untrusted data.

The stdio lifecycle supports MCP `initialize`, `tools/list`, and `tools/call`.
EOF shuts the server down cleanly. Available tools cover store, search, recall,
update, archive, related memories, timeline, conflicts, and stats. Errors are
returned as JSON-RPC data and never include credentials.

Build the Claude Skill archive with:

```bash
redstone skill build
```

Install that archive in the Claude client alongside the MCP configuration. The
Skill defines when durable facts should be stored and when prior state should
be recalled; Redstone core remains deterministic and provider-neutral.
