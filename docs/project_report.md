# Project report

## Summary

This repository implements a Portuguese Labour Code question-answering assistant grounded in retrieved legal excerpts. The product includes a CLI, a Streamlit UI, prompt versioning, and a structured evaluation workflow.

## What is complete

- the app responds to user questions with legal excerpts and citations
- the prompt is versioned under `prompts/`
- the evaluation golden set and deterministic checks exist under `evaluation/`
- the repository keeps a repeatable evaluation procedure in `.github/skills/run-evaluation/SKILL.md`
- the automated test suite passes

## What remains external to the repository

The checklist expects a final public GitHub repo, a deck, a short report, and proof of before/after Copilot behavior. Those items require a public GitHub context and external deliverables that are not available inside this local checkout.

## Current status

The repository is functionally complete as a project implementation, but it is not fully complete as a published final submission package without the external steps listed in the project checklist.

## Evidence used

- `README.md`
- `AGENTS.md`
- `src/app.py`
- `src/web_app.py`
- `src/evaluate_golden_set.py`
- `src/evaluate_judge.py`
- `evaluation/golden_set.json`
- `evaluation/golden_results.json`
- `tests/`

## Limits

This report deliberately avoids claiming public GitHub publication, screenshot evidence, or a final submission deck unless those artifacts are created in the external environment.
