# Copilot steering evidence log

This repository keeps the steering guidance in two places:

- Project-wide guidance in `AGENTS.md` at the repository root.
- Reusable evaluation procedure in `.github/skills/run-evaluation/SKILL.md`.

## What the steering files are intended to control

The guidance in these files is intended to:

- keep all model calls through `ask()` in `src/llm.py`
- prevent secret leakage from `.env`
- preserve prompt versioning under `prompts/`
- require abstention when the law excerpt does not support an answer
- require tests before a code change is considered complete
- force evaluation with explicit limitations and no invented labels

## Current repository evidence

The repository shows the intended steering effects through:

- `AGENTS.md` at the repo root
- `.github/agents/AGENTS.md`
- `.github/skills/run-evaluation/SKILL.md`
- `src/app.py` and `src/evaluate_golden_set.py` using centralized model access logic
- `README.md` documenting the measured limitations of the evaluation

## Important limitation

This repository does not contain a before/after screenshot or a recorded same-request comparison in a Copilot client. The checklist requires that kind of evidence for an external demonstration, but the local repository cannot create or verify that artifact by itself. The evidence stored here is therefore the repository-level proof that the steering files exist and are tied to the intended behavior, not a captured screenshot of an assistant session.
