"""Deterministic question authoring helpers and collection-wide quality checks."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata

KINDS = {"recall", "apply", "trace", "debug", "design"}
LEADS = (
    "A learner is practicing Java fundamentals.",
    "A team discusses a small console exercise.",
    "A developer reviews a Java class.",
    "A student traces a Java program.",
    "A mentor checks a practice project.",
)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def normalize(text: str) -> str:
    """Normalize prose without erasing Java operators, literals or identifier case."""
    text = unicodedata.normalize("NFKC", text).strip()
    for lead in LEADS:
        if text.casefold().startswith(lead.casefold()):
            text = text[len(lead):].strip()
            break
    parts = re.split(r"(```[\s\S]*?```|`[^`]*`)", text)
    return " ".join(
        part.strip() if i % 2 else " ".join(part.casefold().split())
        for i, part in enumerate(parts) if part.strip()
    )


def assessment(objective: str, kind: str, *concepts: str) -> dict:
    return {"objective": objective, "kind": kind, "concepts": sorted(set(concepts))}


def choice(qid: str, prompt: str, answer: str, distractors: list[str],
           explanation: str, topic: str, source: str, intent: dict,
           difficulty: str = "medium") -> dict:
    """Choose a stable answer position from the ID; reordering rows changes nothing."""
    options = [answer, *distractors]
    if len(options) != 4 or len(set(options)) != 4:
        raise ValueError(f"{qid}: supply one answer and three distinct distractors")
    shift = int(hashlib.sha256(qid.encode()).hexdigest()[:8], 16) % 4
    return {
        "id": qid, "revision": 1, "prompt": prompt, "difficulty": difficulty,
        "explanation": explanation, "type": "choice",
        "options": options[shift:] + options[:shift], "correct": [(-shift) % 4],
        "multiple": False, "source_url": source, "topic": topic,
        "assessment": intent, "origin": "ai",
    }


def preserve_revisions(course: dict, previous: dict | None) -> None:
    old_questions = {
        q["id"]: q for test in (previous or {}).get("tests", []) for q in test["questions"]
    }
    # Editorial annotations do not change grading or invalidate an existing attempt.
    editorial = {"revision", "assessment", "source_url", "second_source_url", "origin", "attribution"}
    for test in course["tests"]:
        for q in test["questions"]:
            old = old_questions.get(q["id"])
            if old:
                old_content = {k: v for k, v in old.items() if k not in editorial}
                new_content = {k: v for k, v in q.items() if k not in editorial}
                q["revision"] = old["revision"] + (old_content != new_content)


def audit(courses: list[dict]) -> dict:
    """Fail on known duplication; surface text similarity for editorial review.

    Similarity is a heuristic, never proof that different code behaves identically.
    One objective describes one assessable outcome across the entire collection.
    """
    errors, warnings, summary = [], [], []
    seen = {name: {} for name in ("id", "objective", "prompt", "answer-rationale")}
    by_concept = defaultdict(list)
    for course in courses:
        questions = [q for t in course["tests"] for q in t["questions"]]
        coverage = defaultdict(list)
        for q in questions:
            qid = q["id"]
            meta = q.get("assessment", {})
            objective, kind = meta.get("objective", ""), meta.get("kind")
            concepts = meta.get("concepts", [])
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", objective):
                errors.append(f"{qid}: missing or invalid assessment objective")
            if kind not in KINDS:
                errors.append(f"{qid}: unknown assessment kind {kind!r}")
            if (not concepts or len(set(concepts)) != len(concepts)
                    or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", c) for c in concepts)):
                errors.append(f"{qid}: supply distinct concept slugs")
            if not q.get("source_url", "").startswith("https://"):
                errors.append(f"{qid}: source URL is required")
            if q.get("origin") not in {"ai", "scraped"}:
                errors.append(f"{qid}: origin must be ai or scraped")
            if q.get("origin") == "scraped" and not all(
                q.get("attribution", {}).get(key) for key in ("author", "license", "license_url", "notes")
            ):
                errors.append(f"{qid}: scraped questions require attribution and license information")
            if any(lead.casefold() in q["prompt"].casefold() for lead in LEADS):
                errors.append(f"{qid}: remove the generic narrative lead-in")
            options = q.get("options", [])
            if q.get("type") != "choice" or len(options) != 4:
                errors.append(f"{qid}: the curated bank requires four choice options")
            if len({normalize(o) for o in options}) != len(options):
                errors.append(f"{qid}: duplicate answer options")
            correct = q.get("correct", [])
            if (len(correct) != 1 or q.get("multiple") is not False
                    or any(type(i) is not int or i < 0 or i >= len(options) for i in correct)):
                errors.append(f"{qid}: invalid single-choice answer")
                continue
            answer = tuple(sorted(normalize(options[i]) for i in correct))
            keys = {
                "id": qid, "objective": objective, "prompt": normalize(q["prompt"]),
                "answer-rationale": (tuple(sorted(concepts)), answer, normalize(q["explanation"])),
            }
            for name, key in keys.items():
                if key in seen[name]:
                    errors.append(f"{qid}: duplicate {name} with {seen[name][key]}")
                else:
                    seen[name][key] = qid
            for concept in concepts:
                coverage[concept].append(qid)
                by_concept[concept].append(q)
        summary.append({
            "id": course["id"], "questions": len(questions),
            "skills": dict(sorted(Counter(q.get("assessment", {}).get("kind", "missing") for q in questions).items())),
            "coverage": dict(sorted(coverage.items())),
        })
    compared = set()
    for questions in by_concept.values():
        for index, left in enumerate(questions):
            for right in questions[index + 1:]:
                pair = tuple(sorted((left["id"], right["id"])))
                if pair in compared:
                    continue
                compared.add(pair)
                a, b = normalize(left["prompt"]), normalize(right["prompt"])
                if a != b and SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.85:
                    warnings.append(f"{pair[0]} / {pair[1]}: similar prompts; review the learning outcomes")
    return {"questions": sum(c["questions"] for c in summary), "courses": summary,
            "errors": sorted(errors), "review": sorted(warnings)}


def load_catalog(path: Path) -> list[dict]:
    catalog = json.loads(path.read_text())
    courses = []
    for entry in catalog["courses"]:
        data = (path.parent / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Hash mismatch: {entry['id']}")
        course = json.loads(data)
        if course["id"] != entry["id"]:
            raise ValueError(f"Course ID mismatch: {entry['id']}")
        courses.append(course)
    return courses


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", nargs="?", type=Path, default=Path("content/enterprise/catalog.json"))
    parser.add_argument("--report", type=Path, help="Write the complete coverage and review report")
    args = parser.parse_args()
    report = audit(load_catalog(args.catalog))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    for course in report["courses"]:
        print(f"{course['id']}: {course['questions']} questions, {len(course['coverage'])} concepts; {course['skills']}")
    for message in report["errors"]:
        print(f"ERROR: {message}")
    for message in report["review"]:
        print(f"REVIEW: {message}")
    print(f"{report['questions']} questions; {len(report['errors'])} errors; {len(report['review'])} review pairs")
    raise SystemExit(bool(report["errors"]))
