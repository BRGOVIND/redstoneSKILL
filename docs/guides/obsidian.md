# Obsidian Guide

Initialize a vault and store its path in Redstone configuration:

```bash
redstone obsidian init ~/Documents/Redstone-Vault
```

Export active memories:

```bash
redstone obsidian export
redstone obsidian export --project redstone
redstone obsidian export --type semantic
```

Edit a memory's marked content section in Obsidian, then synchronize:

```bash
redstone obsidian sync
```

Use `redstone obsidian status` to inspect vault state and `redstone obsidian
conflicts` to count unresolved two-sided edits. Redstone never silently
overwrites conflicting edits. Archived memories move to `Archive/`.
