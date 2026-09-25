#!/usr/bin/env python3
"""Build a review map from required concepts to actual chapter headings and sources.

This is a navigation/integrity aid, not a claim that keyword coverage proves accuracy.
The chapter review dates and version baselines remain the editorial source of truth.
"""
import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDY = ROOT / "apps/learner/study"


def audit():
    requirements = json.loads((ROOT / "tests/study-coverage.json").read_text())
    chapters = []
    for topic, concepts in requirements.items():
        body = (STUDY / f"{topic}.md").read_text()
        sections = re.split(r"^## (.+)$", body, flags=re.M)
        evidence = []
        for title, section in zip(sections[1::2], sections[2::2]):
            if title in ("Sources", "Cheatsheet", "Check yourself"):
                continue
            parts = re.split(r"^### (.+)$", section, flags=re.M)
            evidence.append((title, parts[0]))
            evidence.extend((f"{title} / {name}", text)
                            for name, text in zip(parts[1::2], parts[2::2]))
        mapping = {concept: [heading for heading, text in evidence
                             if concept.lower() in (heading + " " + text).lower()]
                   for concept in concepts}
        missing = [concept for concept, matches in mapping.items() if not matches]
        if missing:
            raise ValueError(f"{topic}: concepts only in reference/checklist or missing: {missing}")
        sources = body.split("## Sources", 1)[1].strip()
        chapters.append({
            "topic": topic,
            "prose_words": len(re.sub(r"```.*?```", "", body, flags=re.S).split()),
            "section_ids": [re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                            for title in sections[1::2]],
            "concept_sections": mapping,
            "examples": re.findall(r"^### (Example .+)$", body, re.M),
            "self_checks": body.count("**Answer:**"),
            "review_and_baseline": sources.split("\n\n", 1)[0],
            "sources": re.findall(r"\]\((https://[^)]+)\)", sources),
        })
    return {"chapters": chapters, "totals": {
        "chapters": len(chapters),
        "sections": sum(len(c["section_ids"]) for c in chapters),
        "examples": sum(len(c["examples"]) for c in chapters),
        "self_checks": sum(c["self_checks"] for c in chapters),
        "prose_words": sum(c["prose_words"] for c in chapters),
    }}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["totals"], indent=2))
