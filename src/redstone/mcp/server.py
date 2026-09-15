"""Minimal JSON-RPC MCP server over standard input/output."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from redstone.config import RedstoneConfig
from redstone.core.manager import MemoryManager
from redstone.storage.sqlite import SQLiteMemoryStore


def _manager(root: str | None) -> MemoryManager:
    base = Path(root).expanduser().resolve() if root else Path.cwd()
    database = RedstoneConfig.load(base).database_path
    return MemoryManager(SQLiteMemoryStore(database if database.is_absolute() else base / database))


TOOLS = [
    "memory_search",
    "memory_recall",
    "memory_store",
    "memory_update",
    "memory_archive",
    "memory_related",
    "memory_timeline",
    "memory_conflicts",
    "memory_stats",
]

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "memory_search": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string"},
            "project": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1},
        },
    },
    "memory_recall": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string"},
            "project": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1},
            "max_tokens": {"type": "integer", "minimum": 1},
        },
    },
    "memory_store": {
        "required": ["content"],
        "properties": {
            "content": {"type": "string"},
            "type": {"type": "string"},
            "source": {"type": "string"},
            "project": {"type": "string"},
            "supersedes": {"type": "string"},
        },
    },
    "memory_update": {
        "required": ["id", "content"],
        "properties": {"id": {"type": "string"}, "content": {"type": "string"}},
    },
    "memory_archive": {
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    },
    "memory_related": {
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    },
    "memory_timeline": {
        "required": ["project"],
        "properties": {"project": {"type": "string"}},
    },
    "memory_conflicts": {"properties": {}},
    "memory_stats": {"properties": {}},
}


def handle_request(request: dict[str, Any], manager: MemoryManager) -> dict[str, Any] | None:
    """Handle one JSON-RPC request for stdio and integration tests."""
    method, params = request.get("method"), request.get("params", {})
    if method == "initialize":
        result: Any = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "redstone", "version": "0.1.0"},
        }
    elif method == "notifications/initialized":
        return None
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": name,
                    "description": "Redstone local memory tool",
                    "inputSchema": {"type": "object", **TOOL_SCHEMAS[name]},
                }
                for name in TOOLS
            ]
        }
    elif method == "tools/call":
        structured = call_tool(params["name"], params.get("arguments", {}), manager)
        result = {
            "content": [{"type": "text", "text": json.dumps(structured, sort_keys=True)}],
            "structuredContent": structured,
        }
    else:
        raise ValueError(f"unsupported method: {method}")
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}


def call_tool(name: str, arguments: dict[str, Any], manager: MemoryManager) -> dict[str, Any]:
    """Execute compact, provider-neutral memory tool response."""
    if name == "memory_search":
        results = manager.search(
            arguments["query"], project=arguments.get("project"), limit=arguments.get("limit", 10)
        )
        return {
            "memories": [
                {
                    "id": item.memory.id,
                    "content": item.memory.content,
                    "score": item.score,
                    "reason": item.reason,
                    "confidence": item.memory.confidence,
                }
                for item in results
            ]
        }
    if name == "memory_recall":
        return {
            "context": manager.recall(
                arguments["query"],
                project=arguments.get("project"),
                limit=arguments.get("limit", 5),
                max_tokens=arguments.get("max_tokens", 500),
            )
        }
    if name == "memory_store":
        supersedes = arguments.get("supersedes")
        if supersedes and manager.store.get(supersedes) is None:
            raise KeyError(f"superseded memory not found: {supersedes}")
        memory, created = manager.remember(
            arguments["content"],
            arguments.get("type", "semantic"),
            source=arguments.get("source", "mcp"),
            project=arguments.get("project"),
        )
        if supersedes:
            if supersedes == memory.id:
                raise ValueError("a memory cannot supersede itself")
            manager.supersede(supersedes, memory.id)
        return {"id": memory.id, "created": created, "supersedes": supersedes}
    if name == "memory_update":
        memory = manager.update(arguments["id"], arguments["content"])
        return {"id": memory.id, "version": memory.version}
    if name == "memory_archive":
        return {"id": manager.archive(arguments["id"]).id, "archived": True}
    if name == "memory_related":
        return {
            "memories": [
                {"id": memory.id, "summary": memory.summary}
                for memory in manager.related(arguments["id"])
            ]
        }
    if name == "memory_timeline":
        return {
            "memories": [
                {
                    "id": memory.id,
                    "summary": memory.summary,
                    "observed_at": memory.observed_at.isoformat(),
                }
                for memory in manager.timeline(arguments["project"])
            ]
        }
    if name == "memory_conflicts":
        return {
            "conflicts": [
                {"left": left.id, "right": right.id} for left, right in manager.conflicts()
            ]
        }
    if name == "memory_stats":
        return manager.stats()
    raise ValueError(f"unknown tool: {name}")


def run_stdio(root: str | None = None) -> None:
    """Serve line-delimited JSON-RPC suitable for local MCP launchers."""
    manager = _manager(root)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request, manager)
            if response is not None:
                print(json.dumps(response), flush=True)
        except (KeyError, TypeError, ValueError) as error:
            print(
                json.dumps({"jsonrpc": "2.0", "id": None, "error": {"message": str(error)}}),
                flush=True,
            )


if __name__ == "__main__":
    run_stdio()
