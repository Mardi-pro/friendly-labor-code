# Project instructions

- Keep the product focused on answering questions about the Portuguese Labour Code using the fetched source excerpts.
- Route every model request through `ask()` in `src/llm.py`; do not create a second LLM client.
- Never read, print, copy, or commit `.env` or its credentials. Use synthetic questions and public legal text for examples and evaluations.
- Keep the answer prompt versioned under `prompts/` and preserve old versions when testing prompt changes.
- Do not invent legal conclusions, model-evaluation results, or human labels. Abstain when the retrieved source does not support an answer.
- Add or update tests for behavior changes and run the unit suite before considering a code change complete. Run the live evaluation only when its model access is configured and its usage is approved.
