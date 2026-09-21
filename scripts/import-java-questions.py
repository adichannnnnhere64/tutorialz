"""Import a reviewed allowlist from a pinned MIT-licensed Java quiz.

The remote JavaScript is parsed as data and is never executed. The allowlist
excludes ambiguous, incorrect, obsolete, and already-covered questions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

from question_bank import assessment, choice

ROOT = Path(__file__).resolve().parents[1]
REVISION = "c1499f5aed8804d21e93ba76f1fa011afdf07d15"
SOURCE = f"https://raw.githubusercontent.com/imtahirnaseer/Java-Quiz-App/{REVISION}/questions.js"
SOURCE_SHA256 = "b5e0ae210e76a9cfd076326da8ea4c9028471e28794969c2d699b5be787e5ebe"
LICENSE_URL = f"https://github.com/imtahirnaseer/Java-Quiz-App/blob/{REVISION}/LICENSE"
REVIEWED = {
    22: ("string-comparison-zero", "String ordering", "0",
         "String.compareTo returns zero when the strings have the same character sequence; negative and positive results indicate lexicographic ordering."),
    59: ("string-is-reference-type", "Primitive and reference types", "String",
         "String is a class, so String values are references. int, char, and boolean are primitive types."),
    60: ("bitwise-and-operator", "Bitwise operators", "&",
         "For integral operands, & computes bitwise AND. The other choices are bitwise OR, XOR, and complement, respectively."),
    63: ("signed-byte-range", "Byte range", "-128 to 127",
         "byte is an 8-bit signed two's-complement integer, with values from -128 through 127."),
    89: ("list-size-method", "List size", "size()",
         "List exposes its element count through size(). Arrays instead have a length field; String has a length() method."),
}


def imported(data: bytes) -> list[dict]:
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Upstream source hash changed; review before updating the pin")
    raw = data.decode()
    array = raw[raw.index("["):raw.rindex("]") + 1]
    # This pinned file uses only these unquoted object keys and JSON values.
    array = re.sub(r"(?m)^(\s*)(numb|question|answer|options):", r'\1"\2":', array)
    rows = {row["numb"]: row for row in json.loads(array)}
    selected = []
    for number, (objective, topic, expected, explanation) in REVIEWED.items():
        row = rows[number]
        if row["answer"] != expected or row["options"].count(expected) != 1:
            raise ValueError(f"Source answer differs from reviewed answer: {number}")
        q = choice(f"java-scraped-{objective}", row["question"], expected,
                   [option for option in row["options"] if option != expected],
                   explanation, topic, SOURCE,
                   assessment(f"java-{objective}", "recall", topic.lower().replace(" ", "-")), "easy")
        # Preserve upstream option order as well as prompt text.
        q["options"] = row["options"]
        q["correct"] = [row["options"].index(expected)]
        q["origin"] = "scraped"
        q["attribution"] = {
            "author": "Tahir Naseer", "license": "MIT", "license_url": LICENSE_URL,
            "notes": f"Source question {number}; prompt and choices imported verbatim. Explanation added by AI.",
        }
        selected.append(q)
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Use an already downloaded copy of the pinned source")
    args = parser.parse_args()
    if args.source:
        data = args.source.read_bytes()
    else:
        with urlopen(SOURCE, timeout=30) as response:
            data = response.read()
    output = ROOT / "content/enterprise/imports/java-quiz-selected.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(imported(data), indent=2, ensure_ascii=False) + "\n")
    print(f"Imported {len(REVIEWED)} reviewed questions into {output.relative_to(ROOT)}")
