from pathlib import Path

from redstone.cli import main


def test_cli_remember_and_search(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    assert main(["--root", str(tmp_path), "remember", "Redstone keeps memories local."]) == 0
    assert main(["--root", str(tmp_path), "search", "memories local"]) == 0
    assert "Redstone keeps memories local." in capsys.readouterr().out


def test_cli_obsidian_init_and_export(tmp_path: Path, capsys) -> None:
    vault = tmp_path / "vault"
    main(["--root", str(tmp_path), "init"])
    main(["--root", str(tmp_path), "remember", "Obsidian export works."])
    assert main(["--root", str(tmp_path), "obsidian", "init", str(vault)]) == 0
    assert main(["--root", str(tmp_path), "obsidian", "export"]) == 0
    assert "exported: 1" in capsys.readouterr().out


def test_cli_builds_skill(capsys) -> None:
    assert main(["skill", "build"]) == 0
    assert "Built" in capsys.readouterr().out
