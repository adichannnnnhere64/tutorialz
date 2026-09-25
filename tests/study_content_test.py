"""Integrity and executable examples for the bundled, Android-only syllabus."""
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDY = ROOT / "apps/learner/study"


class StudyContentTest(unittest.TestCase):
    def test_syllabus_covers_all_exam_subjects(self):
        registry = (ROOT / "apps/learner/src/study/content.rs").read_text()
        ids = re.findall(r'topic!\(\s*"([\w-]+)"', registry)
        self.assertEqual(len(ids), 24)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(set(ids), {p.stem for p in STUDY.glob("*.md")})
        self.assertTrue({"spring", "hibernate", "servlets", "jsp", "core-java",
                         "oop", "patterns", "ejb", "java8", "java9", "jms",
                         "activemq", "testing-deployment", "architecture"} <= set(ids))
        for topic in ids:
            with self.subTest(topic=topic):
                body = (STUDY / f"{topic}.md").read_text()
                self.assertEqual(re.findall(r"^## (.+)$", body, re.M),
                                 ["Understand", "Apply", "Cheatsheet", "Check yourself", "Sources"])
                sections = re.split(r"^## .+$", body, flags=re.M)[1:]
                self.assertTrue(all(len(section.strip()) > 70 for section in sections))
                self.assertIn("**Answer:**", sections[3])
                self.assertRegex(sections[4], r"\]\(https://")
                self.assertNotIn("![", body, "Lessons must not depend on remote images")

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
