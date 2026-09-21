use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
pub const VERSION: u32 = 1;
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Catalog {
    pub schema_version: u32,
    #[serde(default)]
    pub content_revision: u32,
    pub collection_id: String,
    pub courses: Vec<CourseSummary>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct CourseSummary {
    pub id: String,
    pub title: String,
    pub description: String,
    pub subject: String,
    pub difficulty: String,
    pub path: String,
    pub sha256: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Course {
    pub schema_version: u32,
    pub id: String,
    pub title: String,
    pub description: String,
    pub subject: String,
    pub difficulty: String,
    pub lessons: Vec<Lesson>,
    pub tests: Vec<Test>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Lesson {
    pub id: String,
    pub title: String,
    pub markdown: String,
    pub test_ids: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Test {
    pub id: String,
    pub title: String,
    pub description: String,
    pub difficulty: String,
    pub questions: Vec<Question>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Question {
    pub id: String,
    pub revision: u32,
    pub prompt: String,
    pub difficulty: String,
    pub explanation: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub topic: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub second_topic: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub assessment: Option<QuestionAssessment>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin: Option<QuestionOrigin>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_url: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub second_source_url: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub attribution: Option<QuestionAttribution>,
    #[serde(flatten)]
    pub kind: QuestionKind,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct QuestionAssessment {
    pub objective: String,
    pub kind: String,
    pub concepts: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum QuestionOrigin {
    Ai,
    Scraped,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct QuestionAttribution {
    pub author: String,
    pub license: String,
    pub license_url: String,
    pub notes: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum QuestionKind {
    Choice {
        options: Vec<String>,
        correct: Vec<usize>,
        multiple: bool,
    },
    Blanks {
        blanks: Vec<Blank>,
    },
    Java {
        style: JavaStyle,
        starter: String,
        template: String,
        reference: String,
        cases: Vec<JavaCase>,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum JavaStyle {
    Program,
    Snippet,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Blank {
    pub label: String,
    pub accepted: Vec<String>,
    pub case_sensitive: bool,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct JavaCase {
    pub name: String,
    pub stdin: String,
    pub expected: String,
    #[serde(default)]
    pub harness: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum Answer {
    Choice(Vec<usize>),
    Blanks(Vec<String>),
    Code(String),
    Skipped,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Attempt {
    pub id: String,
    pub question_id: String,
    pub revision: u32,
    pub answer: Answer,
    pub correct: bool,
    pub timestamp: u64,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Session {
    pub id: String,
    pub questions: Vec<Question>,
    pub answers: BTreeMap<String, Attempt>,
    #[serde(default)]
    pub drafts: BTreeMap<String, Answer>,
    #[serde(default)]
    pub fast_mode: bool,
    pub position: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Progress {
    pub schema_version: u32,
    pub collection_id: String,
    pub lessons: BTreeSet<String>,
    pub attempts: Vec<Attempt>,
    pub active: Option<Session>,
}
impl Progress {
    pub fn new(collection: &str) -> Self {
        Self {
            schema_version: VERSION,
            collection_id: collection.into(),
            lessons: BTreeSet::new(),
            attempts: vec![],
            active: None,
        }
    }
    pub fn latest(&self, q: &Question) -> Option<&Attempt> {
        self.attempts
            .iter()
            .filter(|a| {
                a.question_id == q.id && a.revision == q.revision && a.answer != Answer::Skipped
            })
            .max_by_key(|a| a.timestamp)
    }
    pub fn merge(&mut self, other: Self) -> Result<(), String> {
        other.validate()?;
        if self.collection_id != other.collection_id {
            return Err("This backup belongs to another content collection.".into());
        }
        let mut ids: BTreeSet<String> = self.attempts.iter().map(|a| a.id.clone()).collect();
        for a in other.attempts {
            if ids.insert(a.id.clone()) {
                self.attempts.push(a);
            }
        }
        self.lessons.extend(other.lessons);
        if self.active.is_none() {
            self.active = other.active;
        }
        Ok(())
    }
    pub fn validate(&self) -> Result<(), String> {
        if self.schema_version != VERSION || self.collection_id.is_empty() {
            return Err("Unsupported progress file.".into());
        }
        let mut ids = BTreeSet::new();
        if self.attempts.iter().any(|a| {
            a.id.is_empty() || a.question_id.is_empty() || a.revision == 0 || !ids.insert(&a.id)
        }) {
            return Err("Invalid or duplicate attempt IDs.".into());
        }
        if let Some(s) = &self.active {
            if s.questions.is_empty() || s.position >= s.questions.len() {
                return Err("Invalid saved session position.".into());
            }
            let mut qids = BTreeSet::new();
            for q in &s.questions {
                validate_question(q)?;
                if !qids.insert(&q.id) {
                    return Err("Duplicate saved question.".into());
                }
            }
            for (id, a) in &s.answers {
                if !s
                    .questions
                    .iter()
                    .any(|q| q.id == *id && a.question_id == *id && a.revision == q.revision)
                {
                    return Err("Invalid saved answer.".into());
                }
            }
        }
        Ok(())
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Pool {
    UnseenFirst,
    Unanswered,
    Incorrect,
    All,
}
pub fn select_questions(
    questions: Vec<Question>,
    progress: &Progress,
    pool: Pool,
    count: usize,
    seed: u64,
) -> Result<Vec<Question>, String> {
    let mut ids = BTreeSet::new();
    let mut eligible: Vec<_> = questions
        .into_iter()
        .filter(|q| ids.insert(q.id.clone()))
        .filter(|q| match pool {
            Pool::Unanswered => progress.latest(q).is_none(),
            Pool::Incorrect => progress.latest(q).is_some_and(|a| !a.correct),
            _ => true,
        })
        .collect();
    if count == 0 || count > eligible.len() {
        return Err(format!(
            "Choose between 1 and {} questions.",
            eligible.len()
        ));
    }
    eligible.sort_by_key(|q| {
        let seen = pool == Pool::UnseenFirst && progress.latest(q).is_some();
        (seen, hash(format!("{seed}:{}", q.id).as_bytes()))
    });
    eligible.truncate(count);
    Ok(eligible)
}
pub fn grade(q: &Question, answer: &Answer) -> Result<bool, String> {
    match (&q.kind, answer) {
        (_, Answer::Skipped) => Ok(false),
        (
            QuestionKind::Choice {
                correct, options, ..
            },
            Answer::Choice(selected),
        ) => {
            if selected.iter().any(|i| *i >= options.len()) {
                return Err("Invalid option.".into());
            }
            let selected: BTreeSet<_> = selected.iter().collect();
            Ok(selected == correct.iter().collect())
        }
        (QuestionKind::Blanks { blanks }, Answer::Blanks(values)) => Ok(blanks.len()
            == values.len()
            && blanks.iter().zip(values).all(|(b, v)| {
                b.accepted.iter().any(|a| {
                    if b.case_sensitive {
                        a.trim() == v.trim()
                    } else {
                        a.trim().to_lowercase() == v.trim().to_lowercase()
                    }
                })
            })),
        (QuestionKind::Java { .. }, Answer::Code(_)) => {
            Err("Java answers require the execution worker.".into())
        }
        _ => Err("Answer type does not match the question.".into()),
    }
}
pub fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
pub fn validate_catalog(c: &Catalog) -> Result<(), String> {
    if c.schema_version != VERSION || c.collection_id.trim().is_empty() {
        return Err("Unsupported or empty catalog.".into());
    }
    let mut ids = BTreeSet::new();
    for s in &c.courses {
        if !safe_id(&s.id)
            || !ids.insert(&s.id)
            || s.title.trim().is_empty()
            || s.path.starts_with('/')
            || s.path.contains("..")
            || s.path.contains(':')
            || s.path.contains('\\')
            || s.sha256.len() != 64
            || !s.sha256.bytes().all(|b| b.is_ascii_hexdigit())
        {
            return Err(format!("Invalid catalog entry: {}", s.id));
        }
    }
    Ok(())
}
/// An older remote catalog must not restore retired questions after an upgrade.
pub fn validate_catalog_update(current: &Catalog, incoming: &Catalog) -> Result<(), String> {
    if current.collection_id == incoming.collection_id
        && incoming.content_revision < current.content_revision
    {
        return Err("The online catalog is older than your current question bank.".into());
    }
    Ok(())
}
pub fn safe_id(s: &str) -> bool {
    !s.is_empty()
        && s.bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}
pub fn validate_courses(courses: &[Course]) -> Result<(), String> {
    let mut ids = BTreeSet::new();
    let mut objectives = BTreeSet::new();
    for c in courses {
        if c.schema_version != VERSION
            || !safe_id(&c.id)
            || c.title.trim().is_empty()
            || c.subject.trim().is_empty()
            || !difficulty(&c.difficulty)
        {
            return Err("Course needs a unique ID, title, subject and valid difficulty.".into());
        }
        if !ids.insert(c.id.clone()) {
            return Err(format!("Duplicate ID: {}", c.id));
        }
        for l in &c.lessons {
            if !safe_id(&l.id)
                || !ids.insert(l.id.clone())
                || l.title.trim().is_empty()
                || l.test_ids
                    .iter()
                    .any(|id| !c.tests.iter().any(|t| &t.id == id))
            {
                return Err(format!("Invalid lesson: {}", l.id));
            }
        }
        for t in &c.tests {
            if !safe_id(&t.id)
                || !ids.insert(t.id.clone())
                || t.title.trim().is_empty()
                || !difficulty(&t.difficulty)
                || t.questions.is_empty()
            {
                return Err(format!("Invalid or empty test: {}", t.id));
            }
            for q in &t.questions {
                if !ids.insert(q.id.clone()) {
                    return Err(format!("Duplicate ID: {}", q.id));
                }
                validate_question(q)?;
                if let Some(assessment) = &q.assessment {
                    if !objectives.insert(&assessment.objective) {
                        return Err(format!(
                            "Duplicate learning objective: {}",
                            assessment.objective
                        ));
                    }
                }
            }
        }
    }
    Ok(())
}
pub fn difficulty(s: &str) -> bool {
    matches!(s, "easy" | "medium" | "hard")
}
pub fn validate_question(q: &Question) -> Result<(), String> {
    if !safe_id(&q.id)
        || q.revision == 0
        || q.prompt.trim().is_empty()
        || q.explanation.trim().is_empty()
        || !difficulty(&q.difficulty)
    {
        return Err(format!("Incomplete question: {}", q.id));
    }
    if let Some(assessment) = &q.assessment {
        if !safe_id(&assessment.objective)
            || !matches!(
                assessment.kind.as_str(),
                "recall" | "apply" | "trace" | "debug" | "design"
            )
            || assessment.concepts.is_empty()
            || assessment.concepts.iter().any(|c| !safe_id(c))
            || assessment.concepts.iter().collect::<BTreeSet<_>>().len()
                != assessment.concepts.len()
        {
            return Err(format!("Invalid assessment metadata: {}", q.id));
        }
    }
    for url in [&q.source_url, &q.second_source_url].into_iter().flatten() {
        if !url.starts_with("https://")
            || url.len() <= "https://".len()
            || url.chars().any(char::is_whitespace)
        {
            return Err(format!("Invalid source URL: {}", q.id));
        }
    }
    if let Some(attribution) = &q.attribution {
        if attribution.author.trim().is_empty()
            || attribution.license.trim().is_empty()
            || attribution.notes.trim().is_empty()
            || !attribution.license_url.starts_with("https://")
            || attribution.license_url.len() <= "https://".len()
            || attribution.license_url.chars().any(char::is_whitespace)
        {
            return Err(format!("Invalid question attribution: {}", q.id));
        }
    }
    if q.origin == Some(QuestionOrigin::Scraped)
        && (q.source_url.is_none() || q.attribution.is_none())
    {
        return Err(format!(
            "Scraped question needs a source and attribution: {}",
            q.id
        ));
    }
    let valid = match &q.kind {
        QuestionKind::Choice {
            options,
            correct,
            multiple,
        } => {
            options.len() >= 2
                && options.iter().all(|s| !s.trim().is_empty())
                && options
                    .iter()
                    .map(|s| s.trim())
                    .collect::<BTreeSet<_>>()
                    .len()
                    == options.len()
                && !correct.is_empty()
                && (*multiple || correct.len() == 1)
                && correct.iter().all(|i| *i < options.len())
                && correct.iter().collect::<BTreeSet<_>>().len() == correct.len()
        }
        QuestionKind::Blanks { blanks } => {
            !blanks.is_empty()
                && blanks.iter().all(|b| {
                    !b.label.trim().is_empty()
                        && !b.accepted.is_empty()
                        && b.accepted.iter().all(|a| !a.trim().is_empty())
                })
        }
        QuestionKind::Java {
            style,
            template,
            reference,
            cases,
            ..
        } => {
            !reference.trim().is_empty()
                && !cases.is_empty()
                && cases.iter().all(|c| !c.name.is_empty())
                && (*style == JavaStyle::Program || template.matches("{{answer}}").count() == 1)
        }
    };
    if valid {
        Ok(())
    } else {
        Err(format!("Invalid answer settings: {}", q.id))
    }
}
pub fn duplicate_prompts(courses: &[Course]) -> Vec<String> {
    let mut seen = BTreeSet::new();
    let mut duplicate = vec![];
    for q in courses
        .iter()
        .flat_map(|c| &c.tests)
        .flat_map(|t| &t.questions)
    {
        if !seen.insert(q.prompt.trim().to_lowercase()) {
            duplicate.push(q.id.clone());
        }
    }
    duplicate
}
pub fn sample_courses() -> Vec<Course> {
    serde_json::from_str(include_str!("../../../content/samples.json"))
        .expect("validated embedded samples")
}

/// The bundled collection gives web and Android the same offline question bank.
pub fn enterprise_courses() -> Vec<Course> {
    [
        include_str!("../../../content/enterprise/basic.json"),
        include_str!("../../../content/enterprise/medium.json"),
        include_str!("../../../content/enterprise/advanced.json"),
        include_str!("../../../content/enterprise/beginner-java.json"),
        include_str!("../../../content/enterprise/oop-medium.json"),
    ]
    .iter()
    .map(|json| serde_json::from_str(json).expect("bundled enterprise course must be valid"))
    .collect()
}
#[cfg(test)]
mod tests {
    use super::*;
    fn questions() -> Vec<Question> {
        sample_courses()
            .into_iter()
            .flat_map(|c| c.tests)
            .flat_map(|t| t.questions)
            .collect()
    }
    fn attempt(q: &Question) -> Attempt {
        Attempt {
            id: "a1".into(),
            question_id: q.id.clone(),
            revision: q.revision,
            answer: Answer::Blanks(vec!["x".into()]),
            correct: false,
            timestamp: 1,
        }
    }
    #[test]
    fn sample_content_is_valid() {
        validate_courses(&sample_courses()).unwrap();
    }
    #[test]
    fn question_provenance_survives_serialization_and_session_snapshots() {
        let courses = enterprise_courses();
        validate_courses(&courses).unwrap();
        for question in courses
            .iter()
            .flat_map(|c| &c.tests)
            .flat_map(|t| &t.questions)
        {
            let encoded = serde_json::to_value(question).unwrap();
            assert!(encoded["origin"].is_string());
            assert!(encoded["assessment"]["objective"].is_string());
            let decoded: Question = serde_json::from_value(encoded).unwrap();
            assert_eq!(*question, decoded);
        }
        let old: Question = serde_json::from_str(
            r#"{"id":"old","revision":1,"prompt":"Choose one","difficulty":"easy","explanation":"One","type":"choice","options":["One","Two"],"correct":[0],"multiple":false}"#,
        ).unwrap();
        assert!(old.origin.is_none());
        assert!(old.assessment.is_none());
        validate_question(&old).unwrap();
    }
    #[test]
    fn scraped_questions_require_attribution_and_safe_sources() {
        let mut q = enterprise_courses()
            .into_iter()
            .flat_map(|c| c.tests)
            .flat_map(|t| t.questions)
            .find(|q| q.origin == Some(QuestionOrigin::Scraped))
            .unwrap();
        validate_question(&q).unwrap();
        q.source_url = Some("javascript:alert(1)".into());
        assert!(validate_question(&q).is_err());
        q.source_url = Some("https://example.com/question".into());
        q.attribution = None;
        assert!(validate_question(&q).is_err());
    }
    #[test]
    fn duplicate_objectives_and_choices_are_rejected() {
        let mut courses = enterprise_courses();
        let assessment = courses[0].tests[0].questions[0].assessment.clone();
        courses[1].tests[0].questions[0].assessment = assessment;
        assert!(validate_courses(&courses)
            .unwrap_err()
            .contains("Duplicate learning objective"));
        let mut q = questions()
            .into_iter()
            .find(|q| matches!(q.kind, QuestionKind::Choice { .. }))
            .unwrap();
        if let QuestionKind::Choice { options, .. } = &mut q.kind {
            options[1] = format!(" {} ", options[0]);
        }
        assert!(validate_question(&q).is_err());
    }
    #[test]
    fn older_catalog_cannot_restore_retired_questions() {
        let current: Catalog =
            serde_json::from_str(include_str!("../../../content/enterprise/catalog.json")).unwrap();
        let mut older = current.clone();
        older.content_revision = 0;
        assert!(validate_catalog_update(&current, &older).is_err());
        assert!(validate_catalog_update(&current, &current).is_ok());
        older.content_revision = current.content_revision + 1;
        assert!(validate_catalog_update(&current, &older).is_ok());
        older.content_revision = 0;
        older.collection_id = "another-collection".into();
        assert!(validate_catalog_update(&current, &older).is_ok());
        let legacy: Catalog =
            serde_json::from_str(include_str!("../../../content/catalog.json")).unwrap();
        assert_eq!(legacy.content_revision, 0);
    }
    #[test]
    fn duplicate_id_across_tests_rejected() {
        let mut c = sample_courses();
        let q = c[0].tests[0].questions[0].clone();
        c[1].tests[0].questions.push(q);
        assert!(validate_courses(&c).is_err());
    }
    #[test]
    fn session_is_unique_and_unseen_first() {
        let q = questions();
        let mut p = Progress::new("sample");
        p.attempts.push(attempt(&q[0]));
        let mut repeated = q.clone();
        repeated.extend(q.clone());
        let s = select_questions(repeated, &p, Pool::UnseenFirst, q.len(), 4).unwrap();
        assert_eq!(s.last().unwrap().id, q[0].id);
        assert_eq!(
            s.iter().map(|q| &q.id).collect::<BTreeSet<_>>().len(),
            s.len()
        );
        assert!(select_questions(q, &p, Pool::All, 100, 4).is_err());
    }
    #[test]
    fn revision_changes_are_unanswered() {
        let mut q = questions()[0].clone();
        let mut p = Progress::new("sample");
        p.attempts.push(attempt(&q));
        assert!(p.latest(&q).is_some());
        q.revision += 1;
        assert!(p.latest(&q).is_none());
    }
    #[test]
    fn imports_are_idempotent_and_keep_local_session() {
        let q = questions();
        let mut a = Progress::new("sample");
        a.active = Some(Session {
            id: "local".into(),
            questions: q.clone(),
            answers: BTreeMap::new(),
            drafts: BTreeMap::new(),
            fast_mode: false,
            position: 0,
        });
        let mut b = Progress::new("sample");
        b.attempts.push(attempt(&q[0]));
        b.active = Some(Session {
            id: "remote".into(),
            questions: q,
            answers: BTreeMap::new(),
            drafts: BTreeMap::new(),
            fast_mode: false,
            position: 0,
        });
        a.merge(b.clone()).unwrap();
        a.merge(b).unwrap();
        assert_eq!(a.attempts.len(), 1);
        assert_eq!(a.active.unwrap().id, "local");
    }
    #[test]
    fn rejects_foreign_backup_and_bad_position() {
        let mut a = Progress::new("a");
        assert!(a.merge(Progress::new("b")).is_err());
        a.active = Some(Session {
            id: "s".into(),
            questions: questions(),
            answers: BTreeMap::new(),
            drafts: BTreeMap::new(),
            fast_mode: false,
            position: usize::MAX,
        });
        assert!(a.validate().is_err());
    }
    #[test]
    fn saved_sessions_without_fast_mode_remain_standard_sessions() {
        let session = Session {
            id: "older".into(),
            questions: questions(),
            answers: BTreeMap::new(),
            drafts: BTreeMap::new(),
            fast_mode: false,
            position: 0,
        };
        let mut saved = serde_json::to_value(session).unwrap();
        saved.as_object_mut().unwrap().remove("fast_mode");
        let restored: Session = serde_json::from_value(saved).unwrap();
        assert!(!restored.fast_mode);
    }
    #[test]
    fn exact_choice_set_and_blank_normalization() {
        let mut q = questions()[0].clone();
        q.kind = QuestionKind::Choice {
            options: vec!["a".into(), "b".into(), "c".into()],
            correct: vec![0, 2],
            multiple: true,
        };
        assert!(!grade(&q, &Answer::Choice(vec![0])).unwrap());
        assert!(grade(&q, &Answer::Choice(vec![2, 0])).unwrap());
        q.kind = QuestionKind::Blanks {
            blanks: vec![Blank {
                label: "x".into(),
                accepted: vec!["Hello".into()],
                case_sensitive: false,
            }],
        };
        assert!(grade(&q, &Answer::Blanks(vec![" hello ".into()])).unwrap());
    }
    #[test]
    fn incorrect_filter_uses_latest_attempt() {
        let q = questions();
        let mut p = Progress::new("s");
        let a = attempt(&q[0]);
        p.attempts.push(a.clone());
        assert_eq!(
            select_questions(q.clone(), &p, Pool::Incorrect, 1, 1)
                .unwrap()
                .len(),
            1,
        );
        p.attempts.push(Attempt {
            id: "a2".into(),
            timestamp: 2,
            correct: true,
            ..a
        });
        assert!(select_questions(q, &p, Pool::Incorrect, 1, 1).is_err());
    }
}
