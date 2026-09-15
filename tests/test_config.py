from pathlib import Path

from redstone.config import RedstoneConfig, initialize_config


def test_init_config_is_non_destructive(tmp_path: Path) -> None:
    path = initialize_config(tmp_path)
    original = path.read_text(encoding="utf-8")
    assert RedstoneConfig.load(tmp_path).top_k == 10
    assert initialize_config(tmp_path).read_text(encoding="utf-8") == original
