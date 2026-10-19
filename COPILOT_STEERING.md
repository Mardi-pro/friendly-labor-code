# Copilot and coding-assistant steering

This note records the repository files used to guide coding assistants, the
behavior each file is intended to influence, and what can be verified from the
repository history. Instructions steer model behavior; they do not guarantee
that a model will follow them.

## Files created at the repository root

- [`Project Guidelines.md`](./Project%20Guidelines.md) is the project pathway
  checklist. It describes the product and its milestones, and calls out the
  intended Copilot setup, including an always-on `AGENTS.md` and a reusable
  evaluation skill. It gives an assistant project context, but is a checklist,
  not itself a machine-enforced instruction file.
- `AGENTS.md` was initially created at the root with guidance for the legal
  assistant: cite applicable Labour Code provisions, use plain language, avoid
  unsupported claims, and explain the limits of the service. It was later
  removed from the root; it is not present there now.

## Current coding-assistant guidance

- [`.github/agents/AGENTS.md`](./.github/agents/AGENTS.md) contains the revised
  project instructions. It directs development toward the Portuguese Labour
  Code product, routes model calls through `ask()` in `src/llm.py`, protects
  `.env` credentials, keeps answer prompts versioned, requires source-supported
  legal answers, and calls for tests and cautious use of the live evaluation.
  The intended effect is to reduce duplicated LLM clients, secret exposure,
  unsupported legal conclusions, and untested changes.
- [`.github/skills/run-evaluation/SKILL.md`](./.github/skills/run-evaluation/SKILL.md)
  defines a repeatable evaluation procedure. When a request is about scoring
  the assistant or its golden set, it directs the assistant to verify the law
  snapshot and model access, run the evaluation, inspect every result, report
  limitations, and avoid inventing human labels or metrics. It also makes the
  model-call and quota implications explicit.

The original root `AGENTS.md` was relocated and rewritten as development
guidance in `.github/agents/AGENTS.md`. Because the root file is now absent and
the instructions live under `.github/agents/`, they should not be described as
verified, repository-wide always-on instructions for every Copilot surface.
The repository history records the file changes, but does not establish which
Copilot clients loaded them.

## Application-domain skills

[`skills/labor-code-verifier/SKILL.md`](./skills/labor-code-verifier/SKILL.md)
and
[`skills/labor-code-question-analysis/SKILL.md`](./skills/labor-code-question-analysis/SKILL.md)
describe legal-answer procedures: find and cite exact provisions, clarify
material facts, apply the source conservatively, and abstain when it does not
support a conclusion. These target the labor-code assistant's answers rather
than coding-agent development behavior. No application code reference to these
skill files was found, so this repository alone does not show that the runtime
loads them.

## Evidence and limits

The files express the intended steering effects above. There is no recorded
same-request before/after Copilot interaction or screenshot in the repository,
so a measured change in model behavior cannot be claimed. Such evidence would
be needed to establish that a given Copilot surface loaded a file and that it
changed the generated result.
