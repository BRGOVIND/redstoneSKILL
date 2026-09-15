"""Local Redstone configuration."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = """[storage]
backend = "sqlite"
database_path = ".redstone/index.db"

[retrieval]
top_k = 10
keyword_weight = 0.70
importance_weight = 0.20
confidence_weight = 0.10

[privacy]
block_secrets = true

[embeddings]
enabled = false
provider = "local"

[obsidian]
enabled = false
vault_path = ""
memory_directory = "Memories"
archive_directory = "Archive"

[mcp]
enabled = true

[skill]
package_path = "dist/redstone-memory.zip"
"""


@dataclass(frozen=True)
class RedstoneConfig:
    """Validated subset of user-editable local configuration."""

    top_k: int = 10
    database_path: Path = Path(".redstone/index.db")
    block_secrets: bool = True
    embeddings_enabled: bool = False
    obsidian_enabled: bool = False
    obsidian_vault_path: Path | None = None
    mcp_enabled: bool = True
    skill_package_path: Path = Path("dist/redstone-memory.zip")

    @classmethod
    def load(cls, root: Path) -> RedstoneConfig:
        path = root / ".redstone" / "config.toml"
        if not path.exists():
            return cls()
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        retrieval = data.get("retrieval", {})
        storage = data.get("storage", {})
        privacy = data.get("privacy", {})
        embeddings = data.get("embeddings", {})
        obsidian = data.get("obsidian", {})
        mcp = data.get("mcp", {})
        skill = data.get("skill", {})
        vault_path = str(obsidian.get("vault_path", "")).strip()
        return cls(
            top_k=int(retrieval.get("top_k", 10)),
            database_path=Path(str(storage.get("database_path", ".redstone/index.db"))),
            block_secrets=bool(privacy.get("block_secrets", True)),
            embeddings_enabled=bool(embeddings.get("enabled", False)),
            obsidian_enabled=bool(obsidian.get("enabled", False)),
            obsidian_vault_path=Path(vault_path).expanduser() if vault_path else None,
            mcp_enabled=bool(mcp.get("enabled", True)),
            skill_package_path=Path(str(skill.get("package_path", "dist/redstone-memory.zip"))),
        )


def initialize_config(root: Path) -> Path:
    """Create default config without overwriting user changes."""
    config_path = root / ".redstone" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return config_path


def configure_obsidian(root: Path, vault_path: Path) -> Path:
    """Enable Obsidian while preserving unrelated configuration sections."""
    config_path = initialize_config(root)
    data = config_path.read_text(encoding="utf-8")
    replacement = (
        "[obsidian]\n"
        "enabled = true\n"
        f'vault_path = "{vault_path.expanduser().resolve().as_posix()}"\n'
        'memory_directory = "Memories"\n'
        'archive_directory = "Archive"\n'
    )
    start = data.find("[obsidian]\n")
    if start >= 0:
        data = data[:start].rstrip() + "\n\n" + replacement
    else:
        data = data.rstrip() + "\n\n" + replacement
    config_path.write_text(data, encoding="utf-8")
    return config_path
