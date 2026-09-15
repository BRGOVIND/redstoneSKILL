# Installation

Redstone requires Python 3.11 or newer.

```bash
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/redstone init
.venv/bin/redstone doctor
.venv/bin/redstone smoke-test
```

On Windows, use `.venv\Scripts\python` and `.venv\Scripts\redstone`. For
development, install `-e ".[dev]"`. Re-running `redstone init` preserves the
database and configuration. `doctor --json` provides machine-readable status;
warnings are optional integrations, while failures return a nonzero exit code.
