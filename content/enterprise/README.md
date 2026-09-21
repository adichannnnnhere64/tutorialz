# Java and Jakarta EE question bank

The collection contains **350 questions**: 164 easy, 166 medium, and 20 advanced. It replaces a 3,200-question bank that counted repeated lead-ins, shuffled distractors, and arbitrary topic pairs as separate assessments.

| Course | Before | Now | Assessment |
| --- | ---: | ---: | --- |
| Enterprise basic | 100 | 100 | One purpose check per concept |
| Enterprise medium | 300 | 100 | One failure diagnosis per concept |
| Enterprise advanced | 1,000 | 20 | Integrated scenarios and tradeoffs |
| Beginner Java | 1,200 | 64 | 59 practical repairs and five reviewed imports |
| Java OOP | 600 | 66 | Code tracing, debugging, application, and design |

The original 100 enterprise concepts and 120 Java/OOP concepts remain covered. Overlapping concepts may share a question: the floating-point default type and `f` suffix share a repair; substitutability and the Liskov contract share a design decision. New OOP coverage includes records, sealed classes, captured variables, mutable map keys, shallow copying, wildcard reads/writes, and constructor dispatch.

Java questions assume **Java 17 without preview features**. Multiple-choice code examples do not require the optional Java runner. [coverage.json](coverage.json) maps concepts to question IDs and lists assessment skills. [QUESTION_CONVENTIONS.md](QUESTION_CONVENTIONS.md) defines the uniqueness algorithm and authoring rules.

## Origins and sources

Every question carries `origin: "ai"` or `origin: "scraped"`. The learner displays **AI** or **Scraped**, source links, and imported attribution. These fields survive studio export, storage, and session snapshots. Older or manually authored questions without an origin remain unlabeled.

The 345 AI questions use original wording checked against Java/Jakarta specifications and primary design references. A documentation reference does not mean a question was scraped.

Five questions are imported from [Tahir Naseer's Java Quiz App](https://github.com/imtahirnaseer/Java-Quiz-App/tree/c1499f5aed8804d21e93ba76f1fa011afdf07d15), source questions 22, 59, 60, 63, and 89. They add String ordering, primitive/reference types, bitwise AND, byte range, and List size. Prompts and choices are imported verbatim; explanations added by AI are identified in the attribution. See the [MIT license and copyright notice](imports/LICENSE-java-quiz.txt). Incorrect, ambiguous, obsolete, and redundant questions from that source were excluded.

## Regeneration and checks

Edit `scripts/enterprise-content.py`, `scripts/advanced_content.py`, `scripts/java_content.py`, or `scripts/oop_content.py`, then run:

```sh
python3 scripts/enterprise-content.py
python3 scripts/question_bank.py
python3 -m unittest discover -s tests -p '*_test.py'
cargo run -p tutorialz-core --locked -- content/enterprise/catalog.json
```

Tests require Python 3.10+ and JDK 17+. They check curriculum coverage, duplicates, provenance, revisions, deterministic generation, hashes, and all 20 OOP trace answers by compiling/running Java. CI runs these checks. Similarity is an editorial aid; it cannot prove that arbitrary paraphrases have different meanings.

Imports are checked in, so ordinary regeneration works offline. Reproduce the reviewed import with `python3 scripts/import-java-questions.py`, or add `--source /path/to/questions.js` for a local copy. The importer verifies a pinned SHA-256 and parses data without executing upstream JavaScript.

## Publication and progress

Web and Android bundle the same five course files. `catalog.json` records their SHA-256 hashes. The default online source remains `https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json`, configurable with `TUTORIALZ_CATALOG_URL`. Publish this directory, including the `imports/` notices, at that repository's root to update online consumers.

This cleanup is catalog `content_revision: 1`; legacy catalogs default to 0. A new build upgrades an older cached default bank and rejects an older online edition, preventing retired duplicates from returning before publication. Custom sources are not replaced with bundled content. Increase the catalog revision for future published editions. The studio preserves imported revisions and increments on export.

Retained questions keep their IDs; changed learner-visible content increments their question revision. New OOP and advanced assessments use new descriptive IDs. Removed duplicate IDs are retired. Historical attempts remain in backups, and active sessions retain their original question snapshots until finished.
