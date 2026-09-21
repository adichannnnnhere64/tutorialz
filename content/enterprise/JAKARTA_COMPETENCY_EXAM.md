# Jakarta Competency Exam

50 original single-answer scenarios for enterprise Java competency practice, with four choices, an explanation, and a primary-source reference for each question. This is independent practice, not an Accenture product, a reproduction of myCompetency questions, or a validated equivalent of its difficulty, timing, or scoring. No official Accenture blueprint or calibration dataset was available for this review.

## Coverage

Each topic has five distinct assessments, one in each knowledge area below. The labels are searchable through question `topic` and `second_topic` metadata. Spelling is normalized from the requested syllabus.

| Topic | Questions |
| --- | ---: |
| Java Spring | 5 |
| Hibernate | 5 |
| Java - Servlets | 5 |
| Java - JSP | 5 |
| Core Java - General | 5 |
| Java - OOPS | 5 |
| Java Design Patterns | 5 |
| Java - EJB | 5 |
| Core Java - Java 9 | 5 |
| Java - JMS | 5 |

The five knowledge areas each contain ten questions:

- Basic, Development, Programming and Configuration Knowledge
- Design, Architecture, Framework and Business-Process Knowledge
- Solutioning, Deployment and Implementation Knowledge
- Tools, Assets, Functional and Domain Knowledge
- Latest Technology and Industry Trends

The exam includes 39 medium and 11 hard questions: 15 application decisions, 18 debugging scenarios, 14 design decisions, and three traces. Difficulty labels are editorial judgments, not measured proficiency scores. Modernization topics include Spring AOT, record embeddables, virtual threads, Pages 4.0 migration, sealed domain models, AI integration boundaries, runtime capability selection, strong encapsulation, and standard delayed messaging. “Latest” denotes modernization knowledge, not a claim that every referenced feature was introduced this year.

## Versions and review

Java 17 is the default; Java 9 and Java 21 scenarios state their versions explicitly. Version-sensitive Hibernate and Jakarta scenarios state their target releases. Spring questions use the documented semantics of proxy-based transaction management and AOT. Historical JMS/JSP/EJB topic names are retained for syllabus familiarity, while modern APIs use Jakarta terminology.

Questions were filtered for a distinct assessable decision, sufficient assumptions, one defensible answer, and distractors about the same mechanism. Repeated wording and redundant assessment objectives are checked across the entire bank. Existing questions and their revisions are preserved. All questions are labeled `origin: ai`; source links support the technical rationale and do not indicate copied exam material. Pattern scenarios apply the cited API or architecture principle to an original problem rather than claiming that the source contains the scenario itself.

The Java code-output answers are compiled and run in the content tests, using `--release 9` or `--release 17` as appropriate on the installed JDK. Framework answers are checked against documentation, not an executable integration environment for every framework. Automated checks cannot establish psychometric equivalence to a private assessment; qualified practitioner review and pilot results would be needed to calibrate that.

## Practice

Open **Jakarta Competency Exam**, choose its practice test, set **Number of questions** to **50**, and keep **Difficulty** at **All difficulties** for the complete exam. Fast mode defers feedback until review. Smaller sessions can be used for study. There is no imposed pass mark or time limit claimed to match Accenture.

Edit `scripts/jakarta_competency_content.py` in the Tutorialz repository, regenerate using `scripts/enterprise-content.py`, and run the content checks before publishing. Catalog revision 2 adds this course without changing the collection ID or existing question identities.
