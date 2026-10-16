Capstone Project — Pathway Checklist
Prompt Engineering and Interaction Design · Hugo Silva
To successfully accomplish the project goals, you need to follow two tracks:
1.	 The Copilot track is the set of files that steer your coding assistant.
2.	The App track is the product itself, generated using your coding assistant: input → LLM/Agents call → output, its data, and its evaluation.
This checklist was prepared to help you understand the boundaries of the project and organize its implementation. Copy this file into your repo so the coding assistant can help you check whether all milestones are accomplished.
Every example uses the project we ran in class: a ticket assistant — paste a customer ticket, get a category, an urgency, and a first-reply draft. Swap in your own idea. Tags such as (S4) point to the session that taught the item.
M1 · Foundations
☐	Team · Split the roles. E.g. A builds the app, B creates and owns the database (if any), the demonstration input set and the evaluation golden set, C writes the Copilot files and keeps the report log.
☑	App · One-sentence problem statement. E.g. “Support agents paste a ticket and get its category, urgency and a reply draft in seconds.” Test: delete the LLM call — if a product remains, rethink the idea. If you cannot demo it in 90 seconds, cut scope. (README)
☑	App · Repo created from project-starter, group LLM key in .env, and python src/app.py returns an answer. E.g. your first commit can be “starter runs”. app.py and llm.py are only examples for the coding assistant; modify them as needed. (Live model requests completed using the local key.)
☑	Copilot · Create AGENTS.md at the repo root with your always-on rules (S4). E.g. “All LLM calls go through ask() in src/llm.py · never open or print .env · synthetic data only · one screen, no login · implement tests and run the eval script before calling a change done.” (AGENTS.md)
☐	Copilot · Before/after evidence for AGENTS.md. Give Copilot the same request without and with the file; screenshot the difference. E.g. without it, Copilot created a second OpenAI client; with it, it reused ask().
M2 · Running skeleton
☑	App · Input → LLM call → output, end to end on one screen. E.g. a text box and an “Analyse” button; the user gives an input (ticket), the app calls ask(system=PROMPT, prompt=ticket) and shows category, urgency and draft response. Ugly is fine; it must run. (src/web_app.py; HTTP smoke test passed.)
☑	App · The prompt that does the work, in its own file (S2, S5). Use label definitions with boundaries, 2–3 examples, a fixed JSON output and an explicit “unknown” exit. E.g. your file name can be prompts/triage_v1.md; keep v1, v2… as iteration evidence. (prompts/labor_code_v1.md)
☐	[Optional] App · Data in the app’s internal database (S3). E.g. SQLite data/app.db with a clauses table (15 synthetic policy clauses the prompt pulls in as context) and a RAG engine that retrieves from clauses.
☐	App · Evaluation traces, in the database or a file (S5, S6). E.g. a traces table or file logging each input, output, prompt version and latency.
☑	Copilot · At least one SKILL.md in .github/skills/<name>/ for a procedure you keep repeating (S4). E.g. run-eval, description: “Use when asked to evaluate or score the app: runs evaluation/run_eval.py and summarises pass rates per check.” Test: ask “how are we doing on the golden set?” without naming it — it should fire. (.github/skills/run-evaluation/SKILL.md; trigger still needs a Copilot interaction test)
☐	[Optional] Copilot · a sub-agent or an MCP server. E.g. a read-only .github/agents/reviewer.agent.md that flags ambiguous golden labels, or .vscode/mcp.json with a SQLite server to query app.db. Hooks are not required.
M3 · Evaluation
☑	App · Run 20+ realistic inputs and read every output — synthetic or public data only. Name what went wrong: this is your failure taxonomy (S5). E.g. “urgency inflated by angry wording (5/20) · draft promises a refund the policy forbids (3/20)”. (20 synthetic cases run and reviewed; nine citation omissions, one in-scope abstention, and 19 judge evidence-quote validation errors; see README.)
☑	App · Golden set of 20+ cases, labelled before you see a score (S5). E.g. evaluation/golden.csv with columns id, ticket, expected_category, expected_urgency, notes. (20 labelled cases in evaluation/golden_set.json.)
☑	App · Deterministic checks in code for everything with a right answer (S5). E.g. check 1 – output parses as JSON · check 2 – category is in the allowed list · check 3 – the evidence quote is a substring of the ticket · check 4 – draft ≤ 120 words · check 5 – category vs gold labels → precision and recall per class. (JSON schema, retrieved-article citations, expected articles, and abstention are checked; 11/20 passed all checks.)
☑	App · LLM-as-a-judge for what code cannot check (S6). One criterion per judge call, evidence quoted before a PASS/FAIL verdict, and an “unknown” exit. E.g. “Does the draft answer the customer’s actual request?” in evaluation/judge_prompt.md. (20 calls completed: 1 PASS, 19 UNKNOWN because the evidence was not quoted exactly; not reliable enough for accuracy claims.)
☐	App · Judge checked against your own hand labels (S6). Pass your 20+ cases through the app, take the drafts from your traces, and hand-label about 20 of them PASS or FAIL in a separate file, e.g. evaluation/draft_labels.csv with columns id, draft, human_verdict, reason. Take PASS as the positive class and report TPR and TNR. E.g. “TPR 0.90, TNR 0.75 on 20 drafts”. (All trace drafts are ready; human verdicts and reasons remain blank.)
M4 · Iterate and measure
☑	App · One number you can defend: the metric, why that one, and what it does not cover. E.g. “We adopted macro-recall 0.78 on 24 cases because …; it does not tell us whether the reply drafts are any good.” It must be honest, not good. (README: 20/20 expected-article retrieval; this does not establish answer correctness.)
☐	App · One change tried, measured, and kept or abandoned with a reason. E.g. “prompt v3 added 8 examples: recall 0.78 → 0.79 at 3× the cost → abandoned, back to v2.”
☐	Copilot · Evidence for every steering file: a commit or screenshot of what changed because of it. The report must show at least two (e.g. AGENTS.md + your skill). E.g. “run-eval fired on ‘score it’ and produced the same table every time.”
M5 · Submit
☐	Deck, 6 slides max, in this order: the idea · the prompt · how you steered Copilot · failure taxonomy and golden set · your number · what you abandoned.
☐	Report, 5 pages max, no appendices: screenshots, the actual prompts, the dataset, the evaluation method and result, what did not work, and the repo link.
☐	Repo made public at submission, link in the report, no commits after the deadline. Check the secrets-scan workflow is green and .env is not in the history.
☐	Demo rehearsed with a timer: 8 minutes (about 4 of slides, 4 live) plus 2 for questions, and a backup recording.
