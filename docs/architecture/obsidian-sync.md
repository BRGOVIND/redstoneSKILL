# Obsidian Synchronization

SQLite remains structured source of truth. Obsidian is a readable mirror with
stable `redstone_id` frontmatter. Filenames are safe presentation details,
never identity.

Sync state lives in `.redstone/sync.json` inside the vault. It records last
synced SQLite and Markdown hashes. Hashes normalize line endings and trailing
whitespace.

- SQLite changed only: write Markdown.
- Markdown changed only: validate, privacy-scan, then update SQLite.
- Neither changed: no write.
- Both changed: write a conflict record under `Conflicts/`; preserve both.

Redstone only imports documents containing valid Redstone frontmatter. Ordinary
Markdown is skipped. Files larger than 1 MB, invalid UTF-8, malformed metadata,
and secret-bearing content are rejected or skipped.
