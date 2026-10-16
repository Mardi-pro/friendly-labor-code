# Draft relevance judge — v1

Evaluate exactly one criterion: **Does the draft answer the user's actual
question using only the supplied legal excerpts, without asserting a rule the
excerpts do not support?**

First identify one exact evidence quote from the draft or supplied excerpts.
Then decide `PASS` if the draft answers the question and is supported, `FAIL`
if it is materially unresponsive or unsupported, and `UNKNOWN` if the supplied
evidence is insufficient to decide. Do not assess style, completeness beyond
this criterion, or legal correctness beyond the excerpts.

Return only this JSON object, with evidence before verdict. For `UNKNOWN`,
provide a short reason in `evidence_quote` instead of claiming a quote:

{"evidence_quote":"exact quote, or a short reason when UNKNOWN","verdict":"PASS"}
