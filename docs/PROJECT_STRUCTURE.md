# Project structure

The repository separates application code, reference material, runnable scripts, and generated audit output.

| Path | Purpose |
| --- | --- |
| `src/blindspot/` | Main Python application, organized by feature area. |
| `src/blindspot1/` | Compatibility package and command-line entry point. |
| `tests/` | Automated test suite. |
| `personas/` | Example persona profiles used by demos and planning. |
| `scripts/` | Installation, removal, and repeatable demo commands. |
| `dev/experiments/` | One-off diagnostics and exploratory browser experiments; not part of the supported CLI. |
| `docs/` | Technical documentation and saved research references. |
| `reports/` | Generated audit runs and evidence, organized by run ID. Keep local run data here. |
| `.agents/` | Agent skills and instructions used by this project. |
| `.blindspot/` | Local settings, bridge messages, and other machine-specific application state. |
| `browser-use/` | Separate local checkout used when developing the optional browser automation integration. |

## Source package guide

- `ai/`, `config/`: model providers and configuration.
- `browser/`, `runtime/`: browser inspection, session setup, and browser helpers.
- `execution/`: persona task planning, browser actions, safety, and execution results.
- `personas/`, `skills/`, `knowledge/`: task personas, audit playbooks, and reference knowledge.
- `report/`, `reporting/`: compatibility exports and report generation.
- `core/`, `interface/`, `cli.py`: pipeline orchestration and user-facing commands.
- `mcp/`, `web/`: MCP tools and the local web interface.

## Keeping the tree tidy

Run output, Python caches, virtual environments, and machine-local settings are excluded from source control by `.gitignore`. Exploratory scripts belong under `dev/experiments/`; reusable commands belong under `scripts/`; automated checks belong under `tests/`.
