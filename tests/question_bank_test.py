"""Quality and content-integrity checks for the shipped question collection."""
import copy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from question_bank import LEADS, assessment, audit, choice, load_catalog, normalize, preserve_revisions, slug
from oop_content import JAVA_CHECKS
from java_content import BEGINNER

spec = importlib.util.spec_from_file_location("enterprise_content", ROOT / "scripts/enterprise-content.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
installer_spec = importlib.util.spec_from_file_location(
    "install_author_export", ROOT / "scripts/install-author-export.py"
)
installer = importlib.util.module_from_spec(installer_spec)
installer_spec.loader.exec_module(installer)

# Keep the original curriculum independently of whichever questions cover it.
OOP_CONCEPTS = """
Class blueprint|Object instance|Reference identity|Instance state|Static state|
Encapsulation|Data validation|Private access|Public access|Protected access|
Package-private access|Constructor initialization|No-arg constructor|Constructor chaining|
Superclass construction|This reference|Inheritance|Single class inheritance|
Subclass substitutability|Overriding|Override annotation|Overloading|Dynamic dispatch|
Field hiding|Static method hiding|Final method|Final class|Abstract class|Abstract method|
Interface contract|Multiple interfaces|Interface default method|Interface static method|
Composition|Dependency injection|Polymorphic collection|Upcasting|Downcasting|Instanceof test|
Object equality|Hash code contract|ToString representation|Immutable object|Defensive copying|
Interface segregation|Open-closed design|Liskov contract|Single responsibility|Dependency inversion|
Association|Aggregation|Composition ownership|Nested class|Inner class|Anonymous class|
Lambda target|Method reference|Generics|Inheritance and generics|Covariant return
"""


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.courses = load_catalog(ROOT / "content/enterprise/catalog.json")

    def fixture(self):
        return choice("fixture-q", "What does `box.value` contain?", "1", ["2", "3", "4"],
                      "The instance starts at one.", "Instance state", "https://dev.java/learn/",
                      assessment("java-fixture-value", "trace", "instance-state"))

    def check_pair(self, first, second):
        return audit([{"id": "fixture", "tests": [{"questions": [first, second]}]}])

    def test_shipped_bank_passes_quality_checks(self):
        report = audit(self.courses)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["review"], [])
        self.assertEqual(report, json.loads((ROOT / "content/enterprise/coverage.json").read_text()))

    def test_original_curriculum_remains_covered(self):
        coverage = {c["id"]: set(c["coverage"]) for c in audit(self.courses)["courses"]}
        oop = {slug(topic.strip()) for topic in OOP_CONCEPTS.split("|")}
        self.assertEqual(len(oop), 60)
        self.assertEqual(oop - coverage["oop-medium"], set())
        beginner = {slug(row.split("|")[0]) for row in BEGINNER}
        self.assertEqual(beginner - coverage["beginner-java"], set())
        enterprise = {slug(row[1]) for row in generator.ROWS}
        for tier in ("ee-basic", "ee-medium"):
            self.assertEqual(enterprise - coverage[tier], set())

    def test_oop_assesses_reasoning_and_has_no_generic_leads(self):
        oop = next(c for c in self.courses if c["id"] == "oop-medium")
        questions = [q for t in oop["tests"] for q in t["questions"]]
        self.assertEqual({q["assessment"]["kind"] for q in questions}, {"trace", "debug", "design", "apply"})
        for course in self.courses:
            for test in course["tests"]:
                for q in test["questions"]:
                    self.assertFalse(any(lead in q["prompt"] for lead in LEADS), q["id"])

    def test_permuting_options_and_changing_id_does_not_hide_duplicate(self):
        first = self.fixture()
        second = copy.deepcopy(first)
        second["id"] = "different-id"
        second["assessment"]["objective"] = "different-objective"
        answer = second["options"][second["correct"][0]]
        second["options"].reverse()
        second["correct"] = [second["options"].index(answer)]
        second["prompt"] = LEADS[2] + " " + second["prompt"]
        errors = self.check_pair(first, second)["errors"]
        self.assertTrue(any("duplicate prompt" in e for e in errors))
        self.assertTrue(any("duplicate answer-rationale" in e for e in errors))
        self.assertTrue(any("generic narrative" in e for e in errors))

    def test_rephrasing_cannot_reuse_objective(self):
        first, second = self.fixture(), self.fixture()
        second["id"] = "other"
        second["prompt"] = "Which value will be stored after constructing the object?"
        second["explanation"] = "Rephrasing does not create a new learning outcome."
        self.assertTrue(any("duplicate objective" in e for e in self.check_pair(first, second)["errors"]))

    def test_code_normalization_preserves_meaning(self):
        self.assertNotEqual(normalize("Read `Count`"), normalize("Read `count`"))
        self.assertNotEqual(normalize("Test `a != b`"), normalize("Test `a == b`"))
        self.assertNotEqual(normalize('Print `"a  b"`'), normalize('Print `"a b"`'))
        self.assertEqual(normalize("Which   VALUE?"), normalize("which value?"))

    def test_duplicate_option_and_missing_origin_are_rejected(self):
        q = self.fixture()
        q["options"][1] = q["options"][0]
        q.pop("origin")
        errors = audit([{"id": "fixture", "tests": [{"questions": [q]}]}])["errors"]
        self.assertTrue(any("duplicate answer options" in e for e in errors))
        self.assertTrue(any("origin" in e for e in errors))

    def test_scraped_imports_have_license_and_authored_explanation_note(self):
        imported = [q for c in self.courses for t in c["tests"] for q in t["questions"] if q["origin"] == "scraped"]
        self.assertEqual(len(imported), 5)
        for q in imported:
            self.assertEqual(q["attribution"]["license"], "MIT")
            self.assertIn("Explanation added by AI", q["attribution"]["notes"])
            self.assertIn("c1499f5aed8804d21e93ba76f1fa011afdf07d15", q["source_url"])

    def test_revisions_change_only_for_learner_content(self):
        old = {"tests": [{"questions": [self.fixture()]}]}
        old["tests"][0]["questions"][0]["revision"] = 7
        updated = copy.deepcopy(old)
        q = updated["tests"][0]["questions"][0]
        q["assessment"]["objective"] = "new-editorial-objective"
        q["origin"] = "scraped"
        preserve_revisions(updated, old)
        self.assertEqual(q["revision"], 7)
        q["prompt"] = "A meaningfully changed prompt"
        preserve_revisions(updated, old)
        self.assertEqual(q["revision"], 8)

    def test_generation_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            source = ROOT / "content/enterprise"
            catalog = json.loads((source / "catalog.json").read_text())
            names = [entry["path"] for entry in catalog["courses"]] + ["catalog.json", "coverage.json"]
            for name in names:
                shutil.copyfile(source / name, out / name)
            generator.generate(out)
            first = {name: (out / name).read_bytes() for name in names}
            for name in names:
                self.assertEqual(first[name], (source / name).read_bytes(), name)
            generator.generate(out)
            for name in names:
                self.assertEqual(first[name], (out / name).read_bytes(), name)

    def test_jakarta_exam_blueprint(self):
        exam = next(c for c in self.courses if c["id"] == "jakarta-competency-exam")
        self.assertEqual(exam["title"], "Jakarta Competency Exam")
        self.assertEqual(len(exam["tests"]), 1)
        questions = exam["tests"][0]["questions"]
        topics = {"Java Spring", "Hibernate", "Java - Servlets", "Java - JSP",
                  "Core Java - General", "Java - OOPS", "Java Design Patterns",
                  "Java - EJB", "Core Java - Java 9", "Java - JMS"}
        areas = {"Basic, Development, Programming and Configuration Knowledge",
                 "Design, Architecture, Framework and Business-Process Knowledge",
                 "Solutioning, Deployment and Implementation Knowledge",
                 "Tools, Assets, Functional and Domain Knowledge",
                 "Latest Technology and Industry Trends"}
        self.assertEqual(len(questions), 50)
        self.assertEqual(Counter((q["topic"], q["second_topic"]) for q in questions),
                         Counter({(topic, area): 1 for topic in topics for area in areas}))
        for q in questions:
            self.assertEqual(q["origin"], "ai")
            self.assertIn(q["difficulty"], {"medium", "hard"})
            self.assertIn(q["assessment"]["kind"], {"apply", "debug", "design", "trace"})

    def test_jakarta_java_trace_answers(self):
        exam = next(c for c in self.courses if c["id"] == "jakarta-competency-exam")
        questions = exam["tests"][0]["questions"]
        for suffix, release in [("suppressed-close-exception", "17"),
                                ("java-nine-optional-stream", "9")]:
            q = next(q for q in questions if q["id"] == f"jakarta-competency-{suffix}")
            source = q["prompt"].split("```java\n")[1].split("```")[0]
            if "class Main" not in source:
                source = "class Main { public static void main(String[] args) {\n" + source + "\n} }"
            with self.subTest(question=q["id"]), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "Main.java"
                path.write_text(source)
                compiled = subprocess.run(["javac", "--release", release, str(path)],
                                          capture_output=True, text=True, timeout=30)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                actual = subprocess.run(["java", "-cp", temp, "Main"],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertEqual(q["options"][q["correct"][0]], f"`{actual.stdout}`")

    def test_catalog_rejects_modified_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            catalog = json.loads((ROOT / "content/enterprise/catalog.json").read_text())
            entry = catalog["courses"][0]
            catalog["courses"] = [entry]
            (out / "catalog.json").write_text(json.dumps(catalog))
            (out / entry["path"]).write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "Hash mismatch"):
                load_catalog(out / "catalog.json")

    def test_author_export_installs_only_catalog_files(self):
        source = ROOT / "content/enterprise"
        catalog = json.loads((source / "catalog.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "author.zip"
            destination = root / "content"
            destination.mkdir()
            notice = destination / "README.md"
            notice.write_text("keep this notice\n")
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.write(source / "catalog.json", "catalog.json")
                for entry in catalog["courses"]:
                    bundle.write(source / entry["path"], entry["path"])
            installed = installer.install(archive, destination)
            self.assertEqual(len(installed), len(catalog["courses"]) + 1)
            self.assertEqual(notice.read_text(), "keep this notice\n")
            self.assertEqual(
                (destination / "catalog.json").read_bytes(),
                (source / "catalog.json").read_bytes(),
            )

    def test_author_export_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("catalog.json", "{}")
                bundle.writestr("../outside.json", "{}")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                installer.install(archive, root / "content")

    def test_oop_trace_answers_on_java_17(self):
        self.assertIsNotNone(shutil.which("javac"), "Install JDK 17+ to verify question answers")
        by_id = {q["id"]: q for c in self.courses for t in c["tests"] for q in t["questions"]}
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            files = []
            for index, case in enumerate(JAVA_CHECKS):
                directory = out / f"q{index}"
                directory.mkdir()
                path = directory / "Main.java"
                path.write_text(f"package q{index};\n" + case["source"])
                files.append(str(path))
            compile_result = subprocess.run(["javac", "--release", "17", "-d", str(out), *files], capture_output=True, text=True, timeout=60)
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            for index, case in enumerate(JAVA_CHECKS):
                with self.subTest(question=case["id"]):
                    actual = subprocess.run(["java", "-cp", str(out), f"q{index}.Main"], capture_output=True, text=True, timeout=10)
                    self.assertEqual(actual.returncode, 0, actual.stderr)
                    self.assertEqual(actual.stdout, case["stdout"])
                    q = by_id[case["id"]]
                    self.assertEqual(q["options"][q["correct"][0]], f"`{actual.stdout}`")


if __name__ == "__main__":
    unittest.main()
