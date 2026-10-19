# Prompt iteration and measured change log

## Prompt versions in the repository

The project keeps prompt drafts under `prompts/`:

- `labor_code_v1.md`
- `labor_code_v2.md`
- `labor_code_v3.md`
- `labor_code_v4.md`

These versions document the prompt evolution rather than a fully reported benchmark comparison between versions.

## Measured baseline recorded in the repo

The current repository documentation reports the following measured baseline for the golden set in `README.md`:

- retrieval coverage: 20/20 cases found the expected articles
- deterministic checks: 11/20 passed all checks
- judge verdicts: 1 PASS and 19 UNKNOWN, with the latter due to evidence not being an exact quote from the answer or source

These numbers are a valid baseline for the recorded source snapshot, but they are not a claim that a later prompt version improved the result. No before/after prompt-change experiment with numeric deltas was recorded in the repo history that we could verify.

## Decision

The repository keeps the prompt versions and measured baseline, but it does not claim a validated prompt-optimization win beyond the recorded snapshot. Any prompt improvement would need a fresh evaluation run and a documented before/after comparison.
