use dioxus::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tutorialz_core::*;
use tutorialz_ui::*;
fn main() {
    dioxus::launch(App);
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
struct Draft {
    collection_id: String,
    #[serde(default)]
    content_revision: u32,
    courses: Vec<Course>,
    #[serde(default)]
    published: Vec<Course>,
}
impl Default for Draft {
    fn default() -> Self {
        Self {
            collection_id: "tutorialz-samples".into(),
            content_revision: 0,
            courses: sample_courses(),
            published: sample_courses(),
        }
    }
}
#[derive(Clone, Copy)]
struct Context {
    draft: Signal<Draft>,
    course: Signal<usize>,
    tab: Signal<String>,
    message: Signal<String>,
    busy: Signal<bool>,
}
#[component]
fn App() -> Element {
    let draft = use_signal(Draft::default);
    let course = use_signal(|| 0usize);
    let tab = use_signal(|| "Course".to_string());
    let message = use_signal(String::new);
    let busy = use_signal(|| false);
    let mut ready = use_signal(|| false);
    let mut cx = Context {
        draft,
        course,
        tab,
        message,
        busy,
    };
    use_context_provider(|| cx);
    use_future(move || async move {
        match init().await {
            Ok(()) => {
                match load("author-draft").await {
                    Ok(Some(raw)) => match serde_json::from_str(&raw) {
                        Ok(d) => cx.draft.set(d),
                        Err(e) => {
                            cx.message.set(format!("Cannot load draft: {e}"));
                            return;
                        }
                    },
                    Ok(None) => {}
                    Err(e) => {
                        cx.message.set(e);
                        return;
                    }
                }
                ready.set(true);
            }
            Err(e) => cx.message.set(e),
        }
    });
    use_effect(move || {
        if !ready() {
            return;
        }
        let text = serde_json::to_string(&*draft.read()).unwrap();
        spawn(async move {
            if let Err(e) = save("author-draft", &text).await {
                cx.message.set(format!("Draft save failed: {e}"));
            }
        });
    });
    rsx! {
        style { dangerous_inner_html: CSS }
        div { class: "shell",
            aside { class: "sidebar",
                div { class: "brand",
                    span { class: "brand-mark", "t" }
                    "tutorialz"
                }
                div { class: "eyebrow", "CONTENT STUDIO" }
                for (i, c) in draft.read().courses.iter().enumerate() {
                    button {
                        class: if course() == i { "active" } else { "" },
                        onclick: move |_| cx.course.set(i),
                        "{c.title}"
                    }
                }
                button {
                    onclick: move |_| {
                        spawn(async move {
                            let id = uid().await;
                            let c = Course {
                                schema_version: 1,
                                id: format!("course-{id}"),
                                title: "New course".into(),
                                description: String::new(),
                                subject: "General".into(),
                                difficulty: "easy".into(),
                                lessons: vec![],
                                tests: vec![],
                            };
                            let mut d = cx.draft.write();
                            d.courses.push(c);
                            cx.course.set(d.courses.len() - 1);
                        });
                    },
                    "+ New course"
                }
                div { class: "bottom",
                    "Drafts save on this device."
                    br {}
                    "Export, commit, and push."
                }
            }
            main { class: "main",
                div { class: "topline",
                    span { "YOUR CONTENT WORKSHOP" }
                    span { class: "pill", "Separate authoring app" }
                }
                h1 { "Good questions start here." }
                p { class: "intro",
                    "Build a learning path, create thoughtful practice, and publish simple files you own."
                }
                if !message().is_empty() {
                    div { class: "notice", role: "status", "{message}" }
                }
                if ready() {
                    Toolbar {}
                    div { class: "editor-tabs",
                        for name in ["Course", "Lessons", "Tests", "Preview", "JSON"] {
                            button {
                                class: if tab() == name { "primary" } else { "" },
                                onclick: move |_| cx.tab.set(name.into()),
                                "{name}"
                            }
                        }
                    }
                    if let Some(c) = draft.read().courses.get(course()).cloned() {
                        match tab().as_str() {
                            "Lessons" => rsx! {
                                Lessons { key: "{c.id}" }
                            },
                            "Tests" => rsx! {
                                Tests { key: "{c.id}" }
                            },
                            "Preview" => rsx! {
                                Preview { course: c }
                            },
                            "JSON" => rsx! {
                                JsonEditor { key: "{c.id}", course: c }
                            },
                            _ => rsx! {
                                CourseEditor { key: "{c.id}" }
                            },
                        }
                    } else {
                        p { class: "empty", "Create a course to get started." }
                    }
                } else {
                    p { "Opening your drafts…" }
                }
            }
        }
    }
}
#[component]
fn Toolbar() -> Element {
    let mut cx = use_context::<Context>();
    let mut pack_url = use_signal(String::new);
    rsx! {
        div { class: "panel",
            label { class: "field",
                "Content collection ID"
                input {
                    value: cx.draft.read().collection_id.clone(),
                    oninput: move | e | cx.draft
                            .write().collection_id = e.value(),
                }
            }
            div { class: "actions",
                button {
                    disabled: (cx.busy)(),
                    onclick: move |_| {
                        spawn(async move {
                            let result = async {
                                let raw = call("pick", Value::Null).await?;
                                if raw.is_null() {
                                    return Ok(());
                                }
                                let value: Value = serde_json::from_str(
                                        raw.as_str().ok_or("Invalid file")?,
                                    )
                                    .map_err(|e| e.to_string())?;
                                let courses: Vec<Course> = serde_json::from_value(
                                        value["courses"].clone(),
                                    )
                                    .map_err(|e| e.to_string())?;
                                validate_courses(&courses)?;
                                let id = value["catalog"]["collection_id"]
                                    .as_str()
                                    .or(value["collection_id"].as_str())
                                    .ok_or("Missing collection ID")?
                                    .to_string();
                                if !safe_id(&id) {
                                    return Err("Invalid collection ID".into());
                                }
                                cx.draft
                                    .set(Draft {
                                        collection_id: id,
                                        content_revision: serde_json::from_value(
                                            value["catalog"].get("content_revision")
                                                .or_else(|| value.get("content_revision"))
                                                .cloned().unwrap_or(json!(0)),
                                        ).map_err(|e| e.to_string())?,
                                        courses: courses.clone(),
                                        published: courses,
                                    });
                                cx.course.set(0);
                                Ok::<_, String>(())
                            }
                                .await;
                            cx.message.set(result.err().unwrap_or_else(|| "Content imported.".into()));
                        });
                    },
                    "Import bundle"
                }
                button {
                    onclick: move |_| {
                        let text = serde_json::to_string_pretty(&*cx.draft.read()).unwrap();
                        spawn(async move {
                            if let Err(e) = call(
                                    "download",
                                    json!({ "name" : "tutorialz-draft.json", "text" : text }),
                                )
                                .await
                            {
                                cx.message.set(e);
                            }
                        });
                    },
                    "Back up draft"
                }
                button {
                    class: "primary",
                    disabled: (cx.busy)(),
                    onclick: move |_| {
                        spawn(async move {
                            cx.busy.set(true);
                            let mut draft = (cx.draft)();
                            let result = async {
                                if !safe_id(&draft.collection_id) {
                                    return Err(
                                        "Use letters, digits, hyphens or underscores in the collection ID."
                                            .into(),
                                    );
                                }
                                validate_courses(&draft.courses)?;
                                for course in &mut draft.courses {
                                    for test in &mut course.tests {
                                        for q in &mut test.questions {
                                            if let Some(old) = draft
                                                .published
                                                .iter()
                                                .flat_map(|c| &c.tests)
                                                .flat_map(|t| &t.questions)
                                                .find(|old| old.id == q.id)
                                            {
                                                let mut compare = q.clone();
                                                compare.revision = old.revision;
                                                if compare != *old {
                                                    q.revision = q.revision.max(old.revision + 1);
                                                } else {
                                                    q.revision = q.revision.max(old.revision);
                                                }
                                            }
                                            if let QuestionKind::Java { reference, .. } = &q.kind {
                                                cx.message
                                                    .set(format!("Checking reference solution: {}", q.id));
                                                let result = call(
                                                        "java",
                                                        json!({ "question" : q, "source" : reference }),
                                                    )
                                                    .await?;
                                                if result["passed"] != true {
                                                    return Err(
                                                        format!(
                                                            "Reference solution failed for {}: {}",
                                                            q.id,
                                                            result["results"],
                                                        ),
                                                    );
                                                }
                                            }
                                        }
                                    }
                                }
                                let duplicate = duplicate_prompts(&draft.courses);
                                draft.content_revision = draft.content_revision.checked_add(1)
                                    .ok_or("Content revision limit reached")?;
                                call(
                                        "bundle",
                                        json!(
                                            { "collection_id" : draft.collection_id, "content_revision": draft.content_revision, "courses" : draft
                                            .courses }
                                        ),
                                    )
                                    .await?;
                                draft.published = draft.courses.clone();
                                cx.draft.set(draft);
                                Ok::<
                                    _,
                                    String,
                                >(
                                    if duplicate.is_empty() {
                                        "Validated ZIP exported. Unzip into your content repository, then commit and push."
                                            .into()
                                    } else {
                                        format!(
                                            "ZIP exported. Review duplicate prompts: {}",
                                            duplicate.join(", "),
                                        )
                                    },
                                )
                            }
                                .await;
                            cx.message.set(result.unwrap_or_else(|e| e));
                            cx.busy.set(false);
                        });
                    },
                    if (cx.busy)() {
                        "Validating…"
                    } else {
                        "Validate & export ZIP →"
                    }
                }
                if (cx.busy)() {
                    button {
                        onclick: move |_| {
                            spawn(async {
                                let _ = call("cancel", Value::Null).await;
                            });
                        },
                        "Cancel Java check"
                    }
                }
            }
            details {
                summary { "Java compiler pack" }
                p { class: "small muted",
                    "Java reference solutions must pass before export. Install the same optional pack used by the learner app."
                }
                label { class: "field",
                    "Pack directory URL"
                    input {
                        value: pack_url(),
                        oninput: move |e| pack_url.set(e.value()),
                        placeholder: "https://your-site.example/java-pack/",
                    }
                }
                button {
                    disabled: (cx.busy)(),
                    onclick: move |_| {
                        spawn(async move {
                            cx.busy.set(true);
                            let result = call("installPack", json!(pack_url())).await;
                            cx.message
                                .set(result.err().unwrap_or_else(|| "Java pack installed.".into()));
                            cx.busy.set(false);
                        });
                    },
                    "Install pack"
                }
            }
        }
    }
}
#[component]
fn CourseEditor() -> Element {
    let mut cx = use_context::<Context>();
    let i = (cx.course)();
    let c = cx.draft.read().courses[i].clone();
    let mut confirm = use_signal(|| false);
    rsx! {
        section { class: "panel",
            h2 { "Course details" }
            label { class: "field",
                "Title"
                input {
                    value: c.title,
                    oninput: move | e | cx.draft.write().courses[i]
                            .title = e.value(),
                }
            }
            label { class: "field",
                "Description"
                textarea {
                    rows: 3,
                    value: c.description,
                    oninput: move | e | cx.draft.write().courses[i]
                            .description = e.value(),
                }
            }
            label { class: "field",
                "Subject / language"
                input {
                    value: c.subject,
                    oninput: move | e | cx.draft.write().courses[i].subject = e
                            .value(),
                }
            }
            label { class: "field",
                "Difficulty"
                Difficulty {
                    value: c
                            .difficulty,
                    all: false,
                    onchange: move | v | cx.draft.write().courses[i]
                            .difficulty = v,
                }
            }
            p { class: "small muted", "Stable ID: {c.id}" }
            button { class: "danger", onclick: move |_| confirm.set(true), "Delete course" }
            if confirm() {
                div { class: "notice",
                    "Delete this course and all its lessons and questions from your draft?"
                    button {
                        class: "danger",
                        onclick: move |_| {
                            cx.draft.write().courses.remove(i);
                            cx.course.set(0);
                        },
                        "Delete"
                    }
                    button { onclick: move |_| confirm.set(false), "Cancel" }
                }
            }
        }
    }
}
#[component]
fn Lessons() -> Element {
    let mut cx = use_context::<Context>();
    let ci = (cx.course)();
    let mut selected = use_signal(|| 0usize);
    let c = cx.draft.read().courses[ci].clone();
    rsx! {
        div { class: "split",
            div { class: "panel",
                h2 { "Learning path" }
                for (i, l) in c.lessons.iter().enumerate() {
                    button {
                        class: "lesson-button",
                        onclick: move |_| selected.set(i),
                        "{i+1}. {l.title}"
                    }
                }
                button {
                    onclick: move |_| {
                        spawn(async move {
                            let id = uid().await;
                            let mut d = cx.draft.write();
                            let lessons = &mut d.courses[ci].lessons;
                            lessons
                                .push(Lesson {
                                    id: format!("lesson-{id}"),
                                    title: "New lesson".into(),
                                    markdown: "# Your lesson\n\nStart with the idea you want to teach."
                                        .into(),
                                    test_ids: vec![],
                                });
                            selected.set(lessons.len() - 1);
                        });
                    },
                    "+ Add lesson"
                }
            }
            div { class: "panel",
                if let Some(l) = c.lessons.get(selected()) {
                    LessonEditor { key: "{l.id}", index: selected() }
                } else {
                    p { "Add a lesson to begin." }
                }
            }
        }
    }
}
#[component]
fn LessonEditor(index: usize) -> Element {
    let mut cx = use_context::<Context>();
    let ci = (cx.course)();
    let c = cx.draft.read().courses[ci].clone();
    let l = c.lessons[index].clone();
    let mut confirm = use_signal(|| false);
    rsx! {
        label { class: "field",
            "Lesson title"
            input {
                value: l.title,
                oninput: move |
                        e | cx.draft.write().courses[ci].lessons[index].title = e.value(),
            }
        }
        label { class: "field",
            "Study notes (Markdown)"
            textarea {
                class: "code",
                rows: 15,
                value: l.markdown.clone(),
                oninput: move | e | cx.draft.write().courses[ci]
                        .lessons[index].markdown = e.value(),
            }
        }
        details {
            summary { "Preview notes" }
            Markdown { text: l.markdown.clone() }
        }
        h3 { "Associated tests" }
        for t in &c.tests {
            label { class: "test-check",
                input {
                    r#type: "checkbox",
                    checked: l.test_ids
                            .contains(& t.id),
                    onchange: {
                        let id = t.id.clone();
                        move |_| {
                            let mut d = cx.draft.write();
                            let ids = &mut d.courses[ci].lessons[index].test_ids;
                            if ids.contains(&id) {
                                ids.retain(|x| x != &id);
                            } else {
                                ids.push(id.clone());
                            }
                        }
                    },
                }
                "{t.title}"
            }
        }
        div { class: "actions",
            button {
                disabled: index == 0,
                onclick: move |_| cx.draft.write().courses[ci].lessons.swap(index, index - 1),
                "Move up"
            }
            button {
                disabled: index + 1 >= c.lessons.len(),
                onclick: move | _
                        | cx.draft.write().courses[ci].lessons.swap(index, index + 1),
                "Move down"
            }
            button { class: "danger", onclick: move |_| confirm.set(true), "Delete lesson" }
        }
        if confirm() {
            button {
                class: "danger",
                onclick: move |_| {
                    cx.draft.write().courses[ci].lessons.remove(index);
                },
                "Confirm delete"
            }
        }
    }
}
#[component]
fn Tests() -> Element {
    let mut cx = use_context::<Context>();
    let ci = (cx.course)();
    let mut selected = use_signal(|| 0usize);
    let c = cx.draft.read().courses[ci].clone();
    rsx! {
        div { class: "panel",
            h2 { "Practice tests" }
            div { class: "actions",
                for (i, t) in c.tests.iter().enumerate() {
                    button {
                        class: if selected() == i { "primary" } else { "" },
                        onclick: move |_| selected.set(i),
                        "{t.title}"
                    }
                }
                button {
                    onclick: move |_| {
                        spawn(async move {
                            let id = uid().await;
                            let mut d = cx.draft.write();
                            d.courses[ci]
                                .tests
                                .push(Test {
                                    id: format!("test-{id}"),
                                    title: "New test".into(),
                                    description: String::new(),
                                    difficulty: "easy".into(),
                                    questions: vec![],
                                });
                            selected.set(d.courses[ci].tests.len() - 1);
                        });
                    },
                    "+ Add test"
                }
            }
            if let Some(t) = c.tests.get(selected()) {
                TestEditor { key: "{t.id}", index: selected() }
            }
        }
    }
}
#[component]
fn TestEditor(index: usize) -> Element {
    let mut cx = use_context::<Context>();
    let ci = (cx.course)();
    let mut selected = use_signal(|| 0usize);
    let mut confirm = use_signal(|| false);
    let t = cx.draft.read().courses[ci].tests[index].clone();
    rsx! {
        label { class: "field",
            "Test title"
            input {
                value: t.title,
                oninput: move | e
                        | cx.draft.write().courses[ci].tests[index].title = e.value(),
            }
        }
        label { class: "field",
            "Description"
            textarea {
                rows: 2,
                value: t.description,
                oninput: move
                        | e | cx.draft.write().courses[ci].tests[index].description = e.value(),
            }
        }
        label { class: "field",
            "Difficulty"
            Difficulty {
                value: t.difficulty,
                all: false,
                onchange: move |v| cx.draft.write().courses[ci].tests[index].difficulty = v,
            }
        }
        button { class: "danger", onclick: move |_| confirm.set(true), "Delete test" }
        if confirm() {
            button {
                class: "danger",
                onclick: move |_| {
                    let mut d = cx.draft.write();
                    let id = d.courses[ci].tests.remove(index).id;
                    for l in &mut d.courses[ci].lessons {
                        l.test_ids.retain(|x| x != &id);
                    }
                },
                "Confirm delete test & questions"
            }
        }
        hr {}
        div { class: "split",
            div { class: "editor-list",
                for (i, q) in t.questions.iter().enumerate() {
                    button { onclick: move |_| selected.set(i), "{i+1}. {q.prompt}" }
                }
                button {
                    onclick: move |_| {
                        spawn(async move {
                            let id = uid().await;
                            let q = Question {
                                id: format!("question-{id}"),
                                revision: 1,
                                prompt: "Your question?".into(),
                                difficulty: "easy".into(),
                                explanation: "Explain why the answer is correct.".into(),
                                topic: None,
                                second_topic: None,
                                assessment: None,
                                origin: None,
                                source_url: None,
                                second_source_url: None,
                                attribution: None,
                                kind: QuestionKind::Choice {
                                    options: vec!["Option A".into(), "Option B".into()],
                                    correct: vec![0],
                                    multiple: false,
                                },
                            };
                            let mut d = cx.draft.write();
                            let qs = &mut d.courses[ci].tests[index].questions;
                            qs.push(q);
                            selected.set(qs.len() - 1);
                        });
                    },
                    "+ Add question"
                }
            }
            div {
                if let Some(q) = t.questions.get(selected()) {
                    QuestionEditor {
                        key: "{q.id}",
                        test: index,
                        index: selected(),
                        question: q.clone(),
                    }
                }
            }
        }
    }
}
#[component]
fn QuestionEditor(test: usize, index: usize, question: Question) -> Element {
    let mut cx = use_context::<Context>();
    let ci = (cx.course)();
    let mut q = use_signal(|| question.clone());
    let mut settings = use_signal(|| serde_json::to_string_pretty(&question.kind).unwrap());
    let mut error = use_signal(String::new);
    let mut preview = use_signal(|| false);
    let mut confirm = use_signal(|| false);
    use_effect(move || {
        let value = q();
        cx.draft.write().courses[ci].tests[test].questions[index] = value;
    });
    let current = q();
    rsx! {
        label { class: "field",
            "Prompt (Markdown)"
            textarea {
                rows: 3,
                value: current
                        .prompt,
                oninput: move |e| q.write().prompt = e.value(),
            }
        }
        label { class: "field",
            "Difficulty"
            Difficulty {
                value: current.difficulty,
                all: false,
                onchange: move |v| q.write().difficulty = v,
            }
        }
        label { class: "field",
            "Question type"
            select {
                value: match current.kind {
                    QuestionKind::Choice { .. } => "choice",
                    QuestionKind::Blanks { .. } => "blanks",
                    QuestionKind::Java { style: JavaStyle::Program, .. } => "program",
                    _ => "snippet",
                },
                onchange: move |e| {
                    let kind = match e.value().as_str() {
                        "blanks" => {
                            QuestionKind::Blanks {
                                blanks: vec![
                                    Blank {
                                        label: "Answer".into(),
                                        accepted: vec!["answer".into()],
                                        case_sensitive: false,
                                    },
                                ],
                            }
                        }
                        "program" => {
                            QuestionKind::Java {
                                style: JavaStyle::Program,
                                starter: "public class Main { public static void main(String[] args) { } }"
                                    .into(),
                                template: String::new(),
                                reference: "public class Main { public static void main(String[] args) { System.out.println(42); } }"
                                    .into(),
                                cases: vec![
                                    JavaCase {
                                        name: "Example".into(),
                                        stdin: String::new(),
                                        expected: "42".into(),
                                        harness: String::new(),
                                    },
                                ],
                            }
                        }
                        "snippet" => {
                            QuestionKind::Java {
                                style: JavaStyle::Snippet,
                                starter: "return 0;".into(),
                                template: "public class Main { public static int answer() { {{answer}} } }"
                                    .into(),
                                reference: "return 42;".into(),
                                cases: vec![
                                    JavaCase {
                                        name: "Example".into(),
                                        stdin: String::new(),
                                        expected: "42".into(),
                                        harness: "System.out.print(Main.answer());".into(),
                                    },
                                ],
                            }
                        }
                        _ => {
                            QuestionKind::Choice {
                                options: vec!["A".into(), "B".into()],
                                correct: vec![0],
                                multiple: false,
                            }
                        }
                    };
                    settings.set(serde_json::to_string_pretty(&kind).unwrap());
                    q.write().kind = kind;
                },
                option { value: "choice", "Multiple choice / select" }
                option { value: "blanks", "Fill in the blanks" }
                option { value: "program", "Whole Java program" }
                option { value: "snippet", "Missing Java code / method" }
            }
        }
        KindFields { question: q }
        details {
            summary { "Advanced answer settings (JSON)" }
            p { class: "small muted",
                "Choice indexes start at 0. For Java, use Main.java and a single {{answer}} placeholder for snippets. Harnesses run each case; expected output is compared exactly except line endings."
            }
            textarea {
                class: "code",
                rows: 16,
                value: settings(),
                oninput: move | e |
                        settings.set(e.value()),
            }
            button {
                onclick: move |_| match serde_json::from_str::<QuestionKind>(&settings()) {
                    Ok(kind) => {
                        q.write().kind = kind;
                        error.set(String::new());
                    }
                    Err(e) => error.set(e.to_string()),
                },
                "Apply answer JSON"
            }
        }
        if !error().is_empty() {
            p { class: "notice error", "{error}" }
        }
        label { class: "field",
            "Explanation (Markdown)"
            textarea {
                rows: 4,
                value: current.explanation,
                oninput: move | e | q.write().explanation = e
                        .value(),
            }
        }
        p { class: "small muted",
            "{current.id} · revision {current.revision}. Changed questions receive a new revision on export."
        }
        div { class: "actions",
            button { onclick: move | _ | preview.set(!
                        preview()), "Preview question" }
            button {
                onclick: move |_| {
                    let mut copy = q();
                    spawn(async move {
                        copy.id = format!("question-{}", uid().await);
                        copy.revision = 1;
                        cx.draft.write().courses[ci].tests[test].questions.push(copy);
                    });
                },
                "Duplicate"
            }
            button {
                disabled: index == 0,
                onclick: move | _ | cx.draft
                        .write().courses[ci].tests[test].questions.swap(index, index - 1),
                "Move up"
            }
            button {
                disabled: index + 1 >= cx.draft.read().courses[ci].tests[test]
                        .questions.len(),
                onclick: move | _ | cx.draft.write().courses[ci].tests[test]
                        .questions.swap(index, index + 1),
                "Move down"
            }
            button { class: "danger", onclick: move |_| confirm.set(true), "Delete" }
        }
        if confirm() {
            button {
                class: "danger",
                onclick: move |_| {
                    cx.draft.write().courses[ci].tests[test].questions.remove(index);
                },
                "Confirm delete question"
            }
        }
        if preview() {
            QuestionPreview { key: "preview-{q.read().id}", question: q() }
        }
    }
}
#[component]
fn KindFields(question: Signal<Question>) -> Element {
    let mut q = question;
    match q().kind {
        QuestionKind::Choice {
            options,
            correct,
            multiple,
        } => {
            rsx! {
                label { class: "test-check",
                    input {
                        r#type: "checkbox",
                        checked: multiple,
                        onchange: move |e| {
                            if let QuestionKind::Choice { multiple, correct, .. } = &mut q.write().kind {
                                *multiple = e.checked();
                                if !*multiple {
                                    correct.truncate(1);
                                }
                            }
                        },
                    }
                    "Allow multiple correct choices"
                }
                for (i, option) in options.iter().enumerate() {
                    div { class: "row",
                        input {
                            r#type: "checkbox",
                            aria_label: format!("Option {} is correct", i + 1),
                            checked: correct.contains(&i),
                            onchange: move |_| {
                                if let QuestionKind::Choice { correct, multiple, .. } = &mut q.write().kind {
                                    if correct.contains(&i) {
                                        correct.retain(|x| *x != i);
                                    } else {
                                        if !*multiple {
                                            correct.clear();
                                        }
                                        correct.push(i);
                                    }
                                }
                            },
                        }
                        input {
                            aria_label: format!("Option {}", i + 1),
                            value: option.clone(),
                            oninput: move |e| {
                                if let QuestionKind::Choice { options, .. } = &mut q.write().kind {
                                    options[i] = e.value();
                                }
                            },
                        }
                        button {
                            onclick: move |_| {
                                if let QuestionKind::Choice { options, correct, .. } = &mut q.write().kind {
                                    options.remove(i);
                                    correct.retain(|x| *x != i);
                                    for n in correct {
                                        if *n > i {
                                            *n -= 1;
                                        }
                                    }
                                }
                            },
                            "Remove"
                        }
                    }
                }
                button {
                    onclick: move |_| {
                        if let QuestionKind::Choice { options, .. } = &mut q.write().kind {
                            options.push("New option".into());
                        }
                    },
                    "+ Option"
                }
            }
        }
        QuestionKind::Blanks { blanks } => {
            rsx! {
                for (i, b) in blanks.iter().enumerate() {
                    label { class: "field",
                        "Blank label"
                        input {
                            value: b.label.clone(),
                            oninput: move |e| {
                                if let QuestionKind::Blanks { blanks } = &mut q.write().kind {
                                    blanks[i].label = e.value();
                                }
                            },
                        }
                    }
                    label { class: "field",
                        "Accepted answers (one per line)"
                        textarea {
                            rows: 2,
                            value: b.accepted
                                            .join("\n"),
                            oninput: move |e| {
                                if let QuestionKind::Blanks { blanks } = &mut q.write().kind {
                                    blanks[i].accepted = e.value().lines().map(String::from).collect();
                                }
                            },
                        }
                    }
                    label { class: "test-check",
                        input {
                            r#type: "checkbox",
                            checked: b.case_sensitive,
                            onchange: move |e| {
                                if let QuestionKind::Blanks { blanks } = &mut q.write().kind {
                                    blanks[i].case_sensitive = e.checked();
                                }
                            },
                        }
                        "Case sensitive"
                    }
                    button {
                        onclick: move |_| {
                            if let QuestionKind::Blanks { blanks } = &mut q.write().kind {
                                blanks.remove(i);
                            }
                        },
                        "Remove blank"
                    }
                }
                button {
                    onclick: move |_| {
                        if let QuestionKind::Blanks { blanks } = &mut q.write().kind {
                            blanks
                                .push(Blank {
                                    label: "Answer".into(),
                                    accepted: vec![],
                                    case_sensitive: false,
                                });
                        }
                    },
                    "+ Blank"
                }
            }
        }
        QuestionKind::Java {
            starter,
            template,
            reference,
            cases,
            style,
        } => {
            rsx! {
                label { class: "field",
                    "Starter code"
                    textarea {
                        class: "code",
                        rows: 5,
                        value: starter,
                        oninput: move |e| {
                            if let QuestionKind::Java { starter, .. } = &mut q.write().kind {
                                *starter = e.value();
                            }
                        },
                    }
                }
                if style == JavaStyle::Snippet {
                    label { class: "field",
                        "Template (insert {{answer}} once)"
                        textarea {
                            class: "code",
                            rows: 5,
                            value: template,
                            oninput: move |e| {
                                if let QuestionKind::Java { template, .. } = &mut q.write().kind {
                                    *template = e.value();
                                }
                            },
                        }
                    }
                }
                label { class: "field",
                    "Reference solution"
                    textarea {
                        class: "code",
                        rows: 6,
                        value: reference,
                        oninput: move |e| {
                            if let QuestionKind::Java { reference, .. } = &mut q.write().kind {
                                *reference = e.value();
                            }
                        },
                    }
                }
                h3 { "Test cases" }
                for (i, t) in cases.iter().enumerate() {
                    details { open: true,
                        summary { "Case {i+1}" }
                        label { class: "field",
                            "Name"
                            input {
                                value: t.name.clone(),
                                oninput: move |e| {
                                    if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                                        cases[i].name = e.value();
                                    }
                                },
                            }
                        }
                        label { class: "field",
                            "Standard input"
                            textarea {
                                rows: 2,
                                value: t.stdin.clone(),
                                oninput: move |e| {
                                    if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                                        cases[i].stdin = e.value();
                                    }
                                },
                            }
                        }
                        label { class: "field",
                            "Expected output"
                            textarea {
                                rows: 2,
                                value: t.expected.clone(),
                                oninput: move |e| {
                                    if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                                        cases[i].expected = e.value();
                                    }
                                },
                            }
                        }
                        label { class: "field",
                            "Harness statements (empty calls Main.main)"
                            textarea {
                                class: "code",
                                rows: 2,
                                value: t.harness.clone(),
                                oninput: move |e| {
                                    if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                                        cases[i].harness = e.value();
                                    }
                                },
                            }
                        }
                        button {
                            onclick: move |_| {
                                if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                                    cases.remove(i);
                                }
                            },
                            "Remove case"
                        }
                    }
                }
                button {
                    onclick: move |_| {
                        if let QuestionKind::Java { cases, .. } = &mut q.write().kind {
                            cases
                                .push(JavaCase {
                                    name: "New case".into(),
                                    stdin: String::new(),
                                    expected: String::new(),
                                    harness: String::new(),
                                });
                        }
                    },
                    "+ Test case"
                }
            }
        }
    }
}
#[component]
fn QuestionPreview(question: Question) -> Element {
    let mut answer = use_signal(|| initial_answer(&question));
    let mut result = use_signal(String::new);
    let mut busy = use_signal(|| false);
    let q = question.clone();
    rsx! {
        div { class: "panel",
            span { class: "badge", "Learner preview" }
            Markdown { text: question.prompt.clone() }
            QuestionSource { question: question.clone() }
            AnswerFields {
                question: question.clone(),
                answer: answer(),
                disabled: busy(),
                onchange: move |v| answer.set(v),
            }
            button {
                disabled: busy(),
                onclick: move |_| {
                    let q = q.clone();
                    spawn(async move {
                        busy.set(true);
                        let grade = if let Answer::Code(source) = answer() {
                            call("java", json!({ "question" : q, "source" : source }))
                                .await
                                .map(|v| v["passed"] == true)
                        } else {
                            grade(&q, &answer())
                        };
                        result
                            .set(
                                match grade {
                                    Ok(true) => "Correct".into(),
                                    Ok(false) => "Incorrect".into(),
                                    Err(e) => e,
                                },
                            );
                        busy.set(false);
                    });
                },
                "Check preview answer"
            }
            if !result().is_empty() {
                p { class: "notice", "{result}" }
                Markdown { text: question.explanation.clone() }
                Markdown { text: solution(&question) }
            }
        }
    }
}
#[component]
fn Preview(course: Course) -> Element {
    rsx! {
        div { class: "panel",
            h1 { "{course.title}" }
            p { "{course.description}" }
            for l in course.lessons {
                h2 { "{l.title}" }
                Markdown { text: l.markdown.clone() }
            }
            for t in course.tests {
                h2 { "{t.title}" }
                for q in t.questions {
                    QuestionPreview { key: "{q.id}", question: q }
                }
            }
        }
    }
}
#[component]
fn JsonEditor(course: Course) -> Element {
    let mut cx = use_context::<Context>();
    let mut text = use_signal(|| serde_json::to_string_pretty(&course).unwrap());
    let mut error = use_signal(String::new);
    let ci = (cx.course)();
    rsx! {
        div { class: "panel",
            h2 { "Course JSON" }
            p { class: "small muted",
                "Advanced editing. Applying replaces this course after validating the whole collection."
            }
            textarea {
                class: "code",
                rows: 30,
                value: text(),
                oninput: move | e | text
                        .set(e.value()),
            }
            button {
                class: "primary",
                onclick: move |_| {

                    match serde_json::from_str::<Course>(&text()) {
                        Ok(c) => {
                            let mut courses = cx.draft.read().courses.clone();
                            courses[ci] = c;
                            match validate_courses(&courses) {
                                Ok(()) => {
                                    cx.draft.write().courses = courses;
                                    error.set("Course updated.".into());
                                }
                                Err(e) => error.set(e),
                            }
                        }
                        Err(e) => error.set(e.to_string()),
                    }
                },
                "Validate & apply JSON"
            }
            p { class: "notice", "{error}" }
        }
    }
}
