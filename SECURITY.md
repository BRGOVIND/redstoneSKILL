# Security Policy

Redstone 0.1.x is the currently supported release line.

## Memory is data

Stored and retrieved memories are untrusted data, never executable
instructions. Instruction-like text may be stored as test or project data, but
must not change system behavior, trigger tools, reveal prompts, or authorize
deletion. Imported Obsidian Markdown has the same trust level.

## Local boundaries

SQLite is the authoritative structured store. Obsidian is an optional
human-readable mirror, MCP is a tool interface, and Claude or another model is a
client. None of those clients becomes the persistence authority. Core memory
operations require no cloud memory service.

The Obsidian importer uses bounded UTF-8 input and confined Redstone-managed
paths. Synchronization preserves conflicting edits instead of silently choosing
one side. These controls reduce risk but are not a formal security proof.

## Secrets

The default privacy policy rejects recognizable API keys, passwords, bearer
tokens, and private-key material before persistence. Detection is deliberately
conservative and cannot guarantee identification of every secret. Do not use
Redstone as a credential store. Configuration, diagnostics, benchmarks, and
reports must never contain live credential values.

## Reporting

Report suspected vulnerabilities privately to the project maintainers. Include
the affected version, reproduction steps, and impact, but never include live
credentials or unrelated personal data. This project does not currently offer
a security SLA or bug-bounty program.
