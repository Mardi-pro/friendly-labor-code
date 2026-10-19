# Slide 1 — Idea

Build a Portuguese Labour Code assistant that answers work-law questions using retrieved excerpts and legal citations.

# Slide 2 — Prompt

The model receives a versioned prompt, retrieves relevant legal text, and returns a structured answer with citations and abstention when the code does not support a conclusion.

# Slide 3 — Copilot steering

The repository keeps root `AGENTS.md` and a reusable evaluation skill. They are intended to keep model calls centralized, protect `.env`, and require source-based legal answers.

# Slide 4 — Failure taxonomy and golden set

The evaluation tests cover retrieval gaps, missing citations, unjustified abstention, and malformed judge evidence. The golden set includes 20 labeled cases.

# Slide 5 — Measured result

The repository documents the metric and the current result: retrieval coverage was 20/20, deterministic checks passed in 11/20 cases, and the judge returned 1 PASS and 19 UNKNOWN because evidence was not provided as exact quotes from source or answer.

# Slide 6 — What was not fully completed

The repo includes the app and evaluation artifacts, but the public submission, before/after Copilot artifact, and final meeting rehearsal still need to be created in the external submission environment.
