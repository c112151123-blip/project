# AGENTS.md — Chat agent instructions for this repository

Purpose
-------
This file gives concise, actionable guidance for AI coding agents working in this workspace. It is intentionally minimal — link to existing docs where available and only include details agents cannot reliably infer.

Project summary
---------------
- Primary language: Python. Primary entrypoint: [1.py](1.py).
- Secondary file: [material.dart](material.dart) (Dart asset, not part of Python server).

Quick run / dev commands (assumptions)
-----------------------------------
- Use Python 3.8+ and a virtual environment:

  python -m venv .venv
  .venv\\Scripts\\activate
  pip install -r requirements.txt  # if present

- To run the server (if `1.py` is the app):

  python 1.py

What agents should know
-----------------------
- Entrypoint: treat `1.py` as the likely server module. Inspect it for `if __name__ == "__main__"` or framework usage (Flask/FastAPI).
- No tests or CI files detected in repository root — do not assume test frameworks are present unless you find them.
- There is no requirements.txt or pyproject.toml in the workspace; if adding dependencies, update one of these files and list precise versions.
- Keep changes minimal and focused; prefer adding short helper functions or tests rather than large refactors without explicit user approval.

Conventions & best practices for edits
-------------------------------------
- Formatting: prefer `black` for Python and `dart format` for Dart files.
- Linters: prefer `flake8`/`ruff` for Python. Add configuration files only when requested.
- When creating new files, include minimal tests and a short README snippet if the change adds notable behaviour.

Suggested next agent customizations
----------------------------------
- Add a `.github/copilot-instructions.md` or expand this file if the project grows.
- Create a small `skill` that runs common checks: `python -m compileall`, `black --check`, and `flake8` (if added).

Notes for maintainers
--------------------
- This file is intentionally short. Link to existing documentation rather than duplicating it. Update this file when the repo gains a build system, tests, or CI.

If this created file looks good, tell me and I can:
- add `.github/copilot-instructions.md` with more opinionated workflows; or
- create a small CI/workflow file that runs linters and tests.
