# Contributing

Redstone welcomes focused bug fixes, tests, documentation, and improvements that
preserve its local-first architecture.

## Development

```bash
python -m venv .venv
python -m pip install -e ".[dev]" build
ruff check .
pytest -q
python scripts/release_check.py
```

Keep changes narrow. Add tests proportional to behavioral risk. Never include
credentials, personal vaults, local databases, generated environments, or
private conversation data. Benchmark changes must identify the dataset,
baseline, provider, context budget, and limitations; do not generalize synthetic
results into real-world claims.

By contributing, you agree that your contribution is licensed under the
project's MIT License and that you will follow the Code of Conduct.
