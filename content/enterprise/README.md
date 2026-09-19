# Java Enterprise / Jakarta EE question bank

This collection contains 100 basic, 300 medium, and 1,000 advanced multiple-choice questions in the Tutorialz catalog format. The questions and explanations are original text based on 100 curated concepts from the official [Jakarta EE 11 specifications](https://jakarta.ee/release/11/). Each question records its specification URL; advanced questions also record the second topic and source used in its paired scenario. No specification text or third-party interview questions are copied into this repository.

`catalog.json` lists the three course files and their SHA-256 hashes. The learner bundles these files for offline use in web and Android builds, then refreshes from the public raw catalog URL when online. To publish this directory as a standalone GitHub repository, put its files at the repository root on the `main` branch. The default URL is `https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json` and can be overridden at build time with `TUTORIALZ_CATALOG_URL`.

Regenerate after editing concept rows in `scripts/enterprise-content.py`:

```sh
python3 scripts/enterprise-content.py
cargo run -p tutorialz-core -- content/enterprise/catalog.json
```

The generator lives in the Tutorialz app repository. It creates original practice prompts from reviewed concept rows, so the counts include scenario variations and paired topics; they are not 1,400 independently researched facts. Review generated questions before using them for hiring or formal assessment.
