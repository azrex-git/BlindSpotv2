# Development-only files

`experiments/` contains temporary or site-specific diagnostics created while investigating browser behavior. These scripts are not part of the supported application interface and are not collected by the automated test suite. Keep reusable checks in `tests/` and repeatable user-facing commands in `scripts/`.

## Contributor environment

From a source checkout, install [uv](https://docs.astral.sh/uv/) once, then run:

```bash
uv sync --extra dev
uv run blindspot1 --help
uv run pytest
```

The project dependencies are declared in the root `pyproject.toml`. Playwright Chromium can be provisioned in a development environment with `uv run playwright install chromium`.
