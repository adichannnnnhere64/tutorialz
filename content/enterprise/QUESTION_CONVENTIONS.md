# Question conventions

## Define one assessable outcome

State what the student must determine before writing the prompt. Predicting mutation through an alias and predicting the effect of parameter reassignment are different outcomes. Renaming a variable, changing a number, or introducing a mentor does not create a different outcome.

```json
{
  "id": "java-oop-alias-mutation",
  "revision": 1,
  "origin": "ai",
  "source_url": "https://docs.oracle.com/javase/specs/jls/se17/html/jls-4.html#jls-4.3.1",
  "assessment": {
    "objective": "java-alias-mutation",
    "kind": "trace",
    "concepts": ["reference-identity"]
  }
}
```

- `id`: stable identity, normally `<domain>-<course>-<outcome>`. Retain existing IDs for retained content. Never reuse retired IDs.
- `objective`: a concrete outcome, unique across the collection. Describe the behavior or decision rather than a cosmetic scenario variant.
- `kind`: `recall`, `apply`, `trace`, `debug`, or `design`, matching the work actually required.
- `concepts`: stable lowercase slugs for concepts needed to solve the question. Several overlapping concepts may share one assessment. These labels are searchable.
- `origin`: `ai` for original AI writing, `scraped` for an actual imported prompt. Reading a specification while writing an original question does not make it scraped.
- `source_url`: a specific reference or pinned upstream source. Imports also require `attribution.author`, `license`, `license_url`, and `notes` identifying adaptations and AI-added explanations.

## Write direct questions

1. Start with the actual code, failure, or decision. Remove generic stories about a learner, mentor, developer, or review.
2. Supply the assumptions that determine the answer: Java version, variable types, package context, ownership, transaction boundaries, and required behavior.
3. Give four distinct choices about the same problem. Distractors should represent plausible misconceptions. Keep choices comparable in detail; avoid identifying the answer solely by length.
4. Explain the mechanism and the likely misconception. Compile/run output examples and check compilation claims against Java 17.
5. Add a question only for a missing outcome or a different application of a concept. Rewording a definition, reversing it into term identification, shuffling choices, or pairing unrelated failures does not justify another entry.

Basic recognition and applied diagnosis may share a concept when they require different outcomes. Repeated practice uses the same question again. Do not impose question-count quotas.

## Duplicate detection

`scripts/question_bank.py` checks the collection before generation writes files:

1. Require unique question and objective IDs, valid skills/concepts, four distinct choices, and provenance.
2. Remove known legacy lead-ins for comparison and reject their presence in new prompts.
3. Normalize Unicode and prose whitespace/case, preserving operators, identifier case, and literal whitespace inside Markdown code.
4. Reject repeated normalized prompts, independently of IDs or option order.
5. Reject repeated concepts + correct answer text + explanation, catching variants that only change unrelated distractors.
6. Flag questions sharing a concept when prompt similarity reaches 0.85 (`SequenceMatcher`). Review these rather than automatically deleting them: a changed Java operator can change the answer.
7. Generate a coverage report, and test the original curriculum independently of the current questions.

The original Jakarta Competency Exam also rejects repeated choice sets regardless of order and flags reused substantive choices (eight or more words). Its prompts are compared against the entire bank for similarity regardless of concept labels. Short shared API names or code outputs are allowed. These additional editorial gates do not change the separate Dummy Exam. Regression fixtures cover renamed concepts and shuffled choices; a clean report is not a substitute for reviewing the actual decisions and distractors.

The core validator also rejects duplicate objective IDs and choice text in studio exports. Assessment metadata is optional for legacy/custom content but required in this generated bank. Human review must still check semantic overlap across related concept names; metadata and text similarity cannot prove uniqueness of meaning.

## Revisions and imports

Correcting an existing assessment retains its ID and increases its question revision for changes to prompt, choices, correct answer, explanation, difficulty, or displayed topics. Identical regeneration or editorial provenance changes do not increase it. A different outcome gets a new ID. Re-running generation must preserve bytes and catalog hashes.

The catalog's `content_revision` tracks publication editions. Increase it for each future edition; deliberate rollback also publishes a newer edition. Active sessions keep their snapshots and historical attempts remain exportable when duplicate IDs are retired.

Import only reviewed questions that fill coverage gaps and have recorded reuse terms. Pin upstream revisions and hashes, retain required notices, and record modifications. Preserve the imported origin rather than labeling copied text as original AI writing.
