"""Integrity and executable examples for the bundled, Android-only syllabus."""
import pathlib
import re
import subprocess
import tempfile
import unittest
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDY = ROOT / "apps/learner/study"


class StudyContentTest(unittest.TestCase):
    def test_syllabus_covers_all_exam_subjects(self):
        registry = (ROOT / "apps/learner/src/study/content.rs").read_text()
        ids = re.findall(r'topic!\(\s*"([\w-]+)"', registry)
        self.assertEqual(len(ids), 24)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(set(ids), {p.stem for p in STUDY.glob("*.md")})
        coverage = json.loads((ROOT / "tests/study-coverage.json").read_text())
        self.assertEqual(set(ids), set(coverage))
        self.assertTrue({"spring", "hibernate", "servlets", "jsp", "core-java",
                         "oop", "patterns", "ejb", "java8", "java9", "jms",
                         "activemq", "testing-deployment", "architecture"} <= set(ids))
        for topic in ids:
            with self.subTest(topic=topic):
                body = (STUDY / f"{topic}.md").read_text()
                for term in coverage[topic]:
                    self.assertIn(term.lower(), body.lower(), f"Missing required concept: {term}")
                self.assertEqual(re.findall(r"^## (.+)$", body, re.M),
                                 ["Understand", "Apply", "Advanced", "Production", "Exam reasoning", "Cheatsheet", "Check yourself", "Sources"])
                sections = re.split(r"^## .+$", body, flags=re.M)[1:]
                self.assertTrue(all(len(section.strip()) > 70 for section in sections))
                self.assertGreaterEqual(sections[6].count("**Answer:**"), 6)
                self.assertGreaterEqual(len(re.findall(r"^### .*Advanced|^### .*advanced", sections[6], re.M)), 3)
                self.assertRegex(sections[7], r"\]\(https://")
                self.assertRegex(sections[7], r"Reviewed 20\d\d-\d\d-\d\d")
                self.assertGreaterEqual(len(re.findall(r"^### Example ", sections[1], re.M)), 3)
                prose = re.sub(r"```.*?```", "", body, flags=re.S)
                self.assertGreaterEqual(len(prose.split()), 1800, "A full chapter needs substantive explanations, not only code/tables")
                self.assertNotIn("![", body, "Lessons must not depend on remote images")

    def test_patterns_have_no_catalog_omissions(self):
        body = (STUDY / "patterns.md").read_text()
        table = body.split("## Cheatsheet\n", 1)[1].split("## Check yourself", 1)[0]
        names = ["Factory Method", "Abstract Factory", "Builder", "Prototype", "Singleton",
                 "Adapter", "Bridge", "Composite", "Decorator", "Facade", "Flyweight", "Proxy",
                 "Chain of Responsibility", "Command", "Interpreter", "Iterator", "Mediator",
                 "Memento", "Observer", "State", "Strategy", "Template Method", "Visitor"]
        for name in names:
            self.assertIn(f"| {name} |", table)
        self.assertIn("Simple Factory, not a separate GoF entry", table)

    def test_labeled_complete_examples(self):
        count = 0
        for chapter in STUDY.glob("*.md"):
            body = chapter.read_text()
            examples = re.findall(r"Complete Java (\d+) program; expected output: `([^`]+)`\.\s*```java\n(.*?)\n```", body, re.S)
            for release, expected, source in examples:
                count += 1
                with self.subTest(chapter=chapter.stem, example=count), tempfile.TemporaryDirectory() as directory:
                    path = pathlib.Path(directory) / "Main.java"
                    path.write_text(source)
                    # Java 21 examples are exercised by the JDK 21 CI job.
                    subprocess.run(["javac", "--release", release, str(path)], check=True, capture_output=True, text=True, timeout=30)
                    result = subprocess.run(["java", "-cp", directory, "Main"], check=True, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.stdout.strip(), expected)
        self.assertGreaterEqual(count, 35)

    def test_complete_java_examples_have_documented_outputs(self):
        for topic, release, expected in [("core-java", 17, "2:2.5:10"),
                                         ("oop", 17, "card"),
                                         ("java8", 8, "2:10"),
                                         ("java9", 9, "2,4")]:
            with self.subTest(topic=topic), tempfile.TemporaryDirectory() as directory:
                body = (STUDY / f"{topic}.md").read_text()
                source = re.search(r"```java\n(.*?)\n```", body, re.S).group(1)
                path = pathlib.Path(directory) / "Main.java"
                path.write_text(source)
                subprocess.run(["javac", "--release", str(release), str(path)],
                               check=True, capture_output=True, text=True)
                result = subprocess.run(["java", "-cp", directory, "Main"],
                                        check=True, capture_output=True, text=True)
                self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
