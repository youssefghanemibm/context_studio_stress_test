# Writing questions that score reliably

How to write questions that `harness/score.py` can score and `harness/verify_corpus.py` can verify.

## Fields

Use the fields in `docs/CONVENTIONS.md` §7 and a category from `questions/CATEGORIES.md`.

- `expected_answer` must be complete. An answer that contains the expected answer, or one of its variants, scores **correct** as a whole.
- `must_include` is a **list of lists**: an AND of OR-groups.
  ```yaml
  must_include: [["14 days", "fortnight", "two weeks"], ["Tier-3"]]
  ```
- `must_not_include` holds stale or trap values, and also injection markers and fake PII.
  - A hit is tolerated when its sentence marks the value as old ("previously", "was", "instead of").
- `evidence`: prefer `{fact_id: ...}` references into `manifests/*.facts.yaml`. Every hop of a multi-hop question needs its own evidence item.

## Numbers, dates and words

- **Numbers:** "25,000", "25k" and "twenty-five thousand" all match. "NOK 40 000" is understood when a currency is next to it.
  - Use bare numbers unless the currency matters, because "£25,000" in a key requires a currency in the answer.
  - "14" never matches "140".
- **Units:** a key string matches only as consecutive words, so "14 days" misses "14 calendar days". Put the number and the unit in separate groups when the wording may vary.
- **Dates:** month-name dates match ISO dates. dd/mm/yyyy dates and times ("16:00" vs "4 pm") are not normalised, so list alternatives.
- **Words:**
  - "Tier-3" matches "Tier 3" but not "Tier3".
  - Write the shortest stem: "approver" matches "approvers".
  - Never use a bare "yes"/"no" as a key; use a phrase ("does not need", "requires CFO countersignature").
- **`unanswerable` and `rejected_format`:** phrase `expected_answer` as a refusal ("Not found in the corpus…"). `must_include` may list extra decline phrasings.
- **Known limitation:** matching is word-based, so "not 14 days" still matches "14 days". Reviewers check partial and wrong verdicts and use `override`.

## Checks to run after writing

```bash
.venv/bin/python -I harness/score.py keycheck          # every expected_answer and variant must score correct
.venv/bin/python -I harness/verify_corpus.py --checks 2  # every evidence item resolves
```
