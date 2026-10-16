# Skill: Labor Code Article Verification

## Purpose

Use this skill whenever a user asks a question about employee rights, employer duties, or legal procedures.

## Execution Steps

1. **Search Database:** Query the embedded labor code database or text chunks for the keywords relevant to the user query.

2. **Extract Exact Clause:** Locate the specific Article number and paragraph.

3. **Draft Response:**

   - State the direct answer simply in the first sentence.

   - Quote or explicitly cite the exact article number.

   - Add a brief plain-language explanation of what it means for the user.

4. **Fallback:** If no matching article is found in the provided database, explicitly state: *"I cannot find a specific provision covering this in the provided labor code text,"* and do not hallucinate an answer.