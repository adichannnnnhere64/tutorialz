# Java Enterprise / Jakarta EE question bank

This collection contains 3,200 multiple-choice questions in the Tutorialz catalog format: 1,300 easy, 900 medium, and 1,000 advanced. That includes 1,200 beginner Java questions and 600 medium OOP questions, in addition to the original Jakarta EE courses. The questions and explanations are original text based on 100 curated enterprise concepts from the official [Jakarta EE 11 specifications](https://jakarta.ee/release/11/) and 120 curated Java concepts from the official [Java language basics](https://dev.java/learn/language-basics/) and [classes and objects](https://dev.java/learn/classes-objects/) tutorials. Each question records a source URL; advanced questions also record the second topic and source used in its paired scenario. No specification text or third-party interview questions are copied into this repository.

`catalog.json` lists the five course files and their SHA-256 hashes. The learner bundles these files for offline use in web and Android builds, then refreshes from the public raw catalog URL when online. To publish this directory as a standalone GitHub repository, put its files at the repository root on the `main` branch. The default URL is `https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json` and can be overridden at build time with `TUTORIALZ_CATALOG_URL`.

Regenerate after editing concept rows in `scripts/enterprise-content.py` or `scripts/java_content.py`:

```sh
python3 scripts/enterprise-content.py
cargo run -p tutorialz-core -- content/enterprise/catalog.json
```

The generators live in the Tutorialz app repository. They create original practice prompts from curated concept rows, so the counts include scenario variations and paired topics; they are not 3,200 independently researched facts. Review generated questions before using them for hiring or formal assessment.
