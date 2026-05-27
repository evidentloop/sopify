# Sopify Shared Writing Standards

All skills (analyze / design / develop) must follow these 6 rules. Each prevents one class of LLM output accident.

## Rule 1: Separate Facts from Inference

- Inferences must be labeled "inferred" or "likely"
- Quantitative claims need a source or calculation method; otherwise use "approximately N" or omit
- Never present guesses as conclusions

## Rule 2: One Concept, One Term

- Use the same name for the same entity throughout; no synonym switching
- Use backticks for code identifiers: ✅ `app_access_token` ❌ application access token

## Rule 3: Minimize Output Scope

- Output scope = task scope; do not add unrequested sections
- No speculative abstractions — do not expand extension points that are not currently needed
- Optional template blocks with no content should be omitted entirely, not left as empty shells

## Rule 4: Formatting

- Use consistent capitalization for proper nouns: ✅ `GitHub` `JavaScript`
- Use standard punctuation consistently
- Code identifiers in backticks

## Rule 5: Paragraph Constraints

- Paragraphs must not exceed 7 lines; one point per paragraph
- Use at most three heading levels (`#` `##` `###`); do not use `####`

## Rule 6: Verifiable References

- File paths, function names, and class name references must actually exist
- Do not reference fabricated APIs, configuration keys, or documentation sections
