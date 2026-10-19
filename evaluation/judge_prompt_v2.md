# Draft relevance judge - v2

Evaluate exactly one criterion: **Does the draft answer the user's actual
question using only the supplied legal excerpts, without asserting a rule the
excerpts do not support?**

First identify evidence, then decide:

- `PASS` if the draft answers the question and is supported by the supplied
  excerpts.
- `FAIL` if the draft is materially unresponsive or asserts something the
  excerpts do not support.
- `UNKNOWN` if the supplied excerpts are insufficient to decide.

For `PASS` or `FAIL`, `evidence_quote` must be copied verbatim as one
contiguous substring from the draft or supplied excerpts. Copy it in the
original language, preserving its spelling, accents, punctuation, and wording.
Do not translate, paraphrase, combine fragments, or add ellipses. Before
returning, check that the exact string occurs in the draft or excerpts. If no
verbatim substring supports a decision, use `UNKNOWN` and give a short reason
instead of inventing or paraphrasing a quote.

Do not assess style, completeness beyond this criterion, or legal correctness
beyond the supplied excerpts.

Return only this JSON object, with evidence before verdict:

{"evidence_quote":"verbatim quote, or a short reason when UNKNOWN","verdict":"PASS"}
