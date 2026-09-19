use dioxus::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use tutorialz_core::*;
use tutorialz_ui::*;
fn main() {
    dioxus::launch(App);
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
struct State {
    catalog_url: String,
    catalog: Option<Catalog>,
    courses: Vec<Course>,
    progress: Progress,
    pack_url: String,
    #[serde(default)]
    last_synced: Option<String>,
}
impl Default for State {
    fn default() -> Self {
        Self {
            catalog_url: option_env!("TUTORIALZ_CATALOG_URL")
                .unwrap_or("https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json")
                .into(),
            catalog: Some(
                serde_json::from_str(include_str!("../../../content/enterprise/catalog.json"))
                    .expect("bundled enterprise catalog must be valid"),
            ),
            courses: enterprise_courses(),
            progress: Progress::new("tutorialz-jakarta-ee"),
            pack_url: option_env!("TUTORIALZ_JAVA_PACK_URL").unwrap_or("").into(),
            last_synced: None,
        }
    }
}
#[derive(Clone, PartialEq)]
enum Page {
    Library,
    Course(String),
    Practice,
    Session,
    Results,
    Settings,
}
#[derive(Clone, Copy)]
struct AppContext {
    state: Signal<State>,
    page: Signal<Page>,
    message: Signal<String>,
    busy: Signal<bool>,
    pack: Signal<bool>,
    syncing: Signal<bool>,
    sync_status: Signal<String>,
}

async fn sync_catalog(
    mut cx: AppContext,
    url: String,
    allow_switch: bool,
) -> Result<String, String> {
    let original = (cx.state)();
    let raw = call("catalog", json!(url)).await?;
    let catalog: Catalog = serde_json::from_str(raw.as_str().ok_or("Invalid catalog response")?)
        .map_err(|e| e.to_string())?;
    validate_catalog(&catalog)?;
    if !allow_switch && catalog.collection_id != original.progress.collection_id {
        return Err(
            "This catalog is a different collection. Confirm the switch in Settings.".into(),
        );
    }
    let mut courses = Vec::with_capacity(catalog.courses.len());
    let mut updated = 0;
    for entry in &catalog.courses {
        let unchanged = original
            .catalog
            .as_ref()
            .and_then(|old| old.courses.iter().find(|c| c.id == entry.id))
            .is_some_and(|old| old.sha256.eq_ignore_ascii_case(&entry.sha256));
        if unchanged {
            if let Some(course) = original.courses.iter().find(|c| c.id == entry.id) {
                courses.push(course.clone());
                continue;
            }
        }
        let raw = call("course", json!({ "url": url, "entry": entry })).await?;
        let course: Course = serde_json::from_str(raw.as_str().ok_or("Invalid course response")?)
            .map_err(|e| e.to_string())?;
        if course.id != entry.id {
            return Err("Course ID mismatch".into());
        }
        courses.push(course);
        updated += 1;
    }
    validate_courses(&courses)?;
    let synced_at = call("nowIso", Value::Null)
        .await?
        .as_str()
        .unwrap_or("")
        .to_string();
    let mut current = cx.state.write();
    if current.catalog_url != original.catalog_url
        || current.progress.collection_id != original.progress.collection_id
    {
        return Err("The catalog changed during sync; please retry.".into());
    }
    if catalog.collection_id != current.progress.collection_id {
        current.progress = Progress::new(&catalog.collection_id);
    }
    current.catalog_url = url;
    current.catalog = Some(catalog);
    current.courses = courses;
    current.last_synced = Some(synced_at);
    Ok(format!(
        "Questions are up to date. {updated} course files downloaded."
    ))
}
#[component]
fn App() -> Element {
    let state = use_signal(State::default);
    let page = use_signal(|| Page::Library);
    let mut message = use_signal(String::new);
    let busy = use_signal(|| false);
    let mut ready = use_signal(|| false);
    let pack = use_signal(|| false);
    let syncing = use_signal(|| false);
    let sync_status = use_signal(String::new);
    let cx = AppContext {
        state,
        page,
        message,
        busy,
        pack,
        syncing,
        sync_status,
    };
    use_context_provider(|| cx);
    use_future(move || async move {
        let mut cx = cx;
        match init().await {
            Ok(()) => {
                match load("learner-state").await {
                    Ok(Some(raw)) => match serde_json::from_str::<State>(&raw) {
                        Ok(s) => {
                            if validate_courses(&s.courses).is_ok() && s.progress.validate().is_ok()
                            {
                                cx.state.set(s)
                            } else {
                                cx.message
                                        .set(
                                            "Saved data is invalid. Your original backup remains in storage; use Settings to import a valid backup."
                                                .into(),
                                        );
                                return;
                            }
                        }
                        Err(e) => {
                            cx.message.set(format!("Cannot read saved data: {e}"));
                            return;
                        }
                    },
                    Ok(None) => {}
                    Err(e) => {
                        cx.message.set(e);
                        return;
                    }
                }
                cx.pack
                    .set(call("packStatus", Value::Null).await.ok() == Some(json!(true)));
                let _ = call("registerOffline", Value::Null).await;
                ready.set(true);
                // Saved questions are ready before the network request starts.
                spawn(async move {
                    let url = cx.state.read().catalog_url.clone();
                    if url.is_empty() {
                        return;
                    }
                    cx.syncing.set(true);
                    cx.sync_status.set("Checking for question updates…".into());
                    let result = sync_catalog(cx, url, false).await;
                    cx.sync_status
                        .set(result.unwrap_or_else(|e| format!("Using cached questions: {e}")));
                    cx.syncing.set(false);
                });
            }
            Err(e) => message.set(e),
        }
    });
    use_effect(move || {
        if !ready() {
            return;
        }
        let raw = serde_json::to_string(&*state.read()).unwrap();
        spawn(async move {
            if let Err(e) = save("learner-state", &raw).await {
                message.set(format!("Progress could not be saved: {e}"));
            }
        });
    });
    let current = page();
    rsx! {
        style { dangerous_inner_html: CSS }
        div { class: "shell",
            aside { class: "sidebar",
                div { class: "brand",
                    span { class: "brand-mark", "t" }
                    "tutorialz"
                }
                Nav { label: "▦  My learning", target: Page::Library }
                Nav { label: "✓  Practice", target: Page::Practice }
                Nav {
                    label: "◷  Session & results",
                    target: if state.read().progress.active.is_some() { Page::Session } else { Page::Results },
                }
                Nav { label: "⚙  Settings & backups", target: Page::Settings }
                div { class: "bottom",
                    "A little practice, every day."
                    br {}
                    "Your progress stays with you."
                }
            }
            main { class: "main",
                div { class: "topline",
                    span { "YOUR PERSONAL LEARNING SPACE" }
                    span { class: "pill", "●  Offline-friendly" }
                }
                if !message().is_empty() {
                    div { class: "notice", role: "status",
                        "{message}"
                        button {
                            class: "quiet",
                            onclick: move | _ |
                                    message.set(String::new()),
                            "Dismiss"
                        }
                    }
                }
                if !ready() {
                    p { class: "notice", "Opening your learning space…" }
                } else {
                    match current {
                        Page::Library => rsx! {
                            Library {}
                        },
                        Page::Course(id) => rsx! {
                            CourseView { id }
                        },
                        Page::Practice => rsx! {
                            Practice {}
                        },
                        Page::Session => rsx! {
                            SessionView {}
                        },
                        Page::Results => rsx! {
                            Results {}
                        },
                        Page::Settings => rsx! {
                            Settings {}
                        },
                    }
                }
            }
        }
    }
}
#[component]
fn Nav(label: String, target: Page) -> Element {
    let mut cx = use_context::<AppContext>();
    let active = (cx.page)() == target;
    rsx! {
        button {
            class: if active { "active" } else { "" },
            onclick: move |_| {
                if !(cx.busy)() {
                    cx.page.set(target.clone());
                    cx.message.set(String::new());
                }
            },
            "{label}"
        }
    }
}
#[component]
fn Library() -> Element {
    let mut cx = use_context::<AppContext>();
    let mut subject = use_signal(|| "all".to_string());
    let mut level = use_signal(|| "all".to_string());
    let mut search = use_signal(String::new);
    let s = (cx.state)();
    let subjects: BTreeSet<_> = s
        .courses
        .iter()
        .map(|c| c.subject.clone())
        .chain(
            s.catalog
                .iter()
                .flat_map(|c| c.courses.iter().map(|c| c.subject.clone())),
        )
        .collect();
    let all = s
        .courses
        .iter()
        .flat_map(|c| &c.tests)
        .flat_map(|t| &t.questions)
        .collect::<Vec<_>>();
    let answered = all
        .iter()
        .filter(|q| s.progress.latest(q).is_some())
        .count();
    let correct = all
        .iter()
        .filter(|q| s.progress.latest(q).is_some_and(|a| a.correct))
        .count();
    let terms: Vec<String> = search()
        .split_whitespace()
        .map(|s| s.to_lowercase())
        .collect();
    let hits: Vec<(String, String, Question)> = if terms.is_empty() {
        Vec::new()
    } else {
        s.courses
            .iter()
            .filter(|c| subject() == "all" || subject() == c.subject)
            .flat_map(|c| {
                c.tests
                    .iter()
                    .flat_map(move |t| t.questions.iter().map(move |q| (c, t, q)))
            })
            .filter(|(_, _, q)| level() == "all" || level() == q.difficulty)
            .filter(|(c, t, q)| {
                let haystack = format!(
                    "{} {} {} {} {}",
                    c.title,
                    t.title,
                    q.prompt,
                    q.topic.as_deref().unwrap_or(""),
                    q.second_topic.as_deref().unwrap_or("")
                )
                .to_lowercase();
                terms.iter().all(|word| haystack.contains(word))
            })
            .map(|(c, t, q)| (c.title.clone(), t.title.clone(), q.clone()))
            .collect()
    };
    rsx! {
        section { class: "hero",
            div {
                div { class: "eyebrow", "MAKE ROOM FOR SOMETHING NEW" }
                h1 { "Small steps. Stronger skills." }
                p { class: "intro",
                    "Explore a subject, put what you know into practice, and build confidence one question at a time."
                }
                button {
                    class: "primary",
                    onclick: move |_| cx.page.set(Page::Practice),
                    "Start practicing  →"
                }
            }
            div { class: "hero-art",
                "✦"
                div { class: "book",
                    b { "a+b" }
                    span {}
                    span {}
                    span {}
                }
            }
        }
        div { class: "stats",
            div { class: "stat",
                span { "YOUR LIBRARY" }
                strong { "{s.courses.len()}" }
                span { "courses ready to explore" }
            }
            div { class: "stat",
                span { "QUESTIONS ANSWERED" }
                strong { "{answered}" }
                span { "small steps forward" }
            }
            div { class: "stat",
                span { "CORRECT ANSWERS" }
                strong { "{correct}" }
                span { "on your latest attempts" }
            }
        }
        div { class: "section-head",
            h2 { "Your next discovery" }
            span { class: "muted small", "Learn at your own pace" }
        }
        div { class: "filters",
            input {
                placeholder: "Search courses, topics, and questions…",
                value: search(),
                oninput: move |e| search.set(e.value()),
                aria_label: "Search questions and topics",
            }
            select {
                aria_label: "Subject",
                value: subject(),
                onchange: move |e| subject.set(e.value()),
                option { value: "all", "All subjects" }
                for name in subjects {
                    option { value: name.clone(), "{name}" }
                }
            }
            Difficulty { value: level(), all: true, onchange: move |v| level.set(v) }
        }
        div { class: "grid",
            for c in s.courses
                .iter()
                .filter(|c| {
                    (subject() == "all" || subject() == c.subject)
                        && (level() == "all" || level() == c.difficulty)
                        && format!("{} {}", c.title, c.description)
                            .to_lowercase()
                            .contains(&search().to_lowercase())
                })
            {
                CourseCard { course: c.clone() }
            }
        }
        if !terms.is_empty() {
            div { class: "section-head",
                h2 { "Question results" }
                span { class: "muted small", "{hits.len()} matching questions" }
            }
            if !hits.is_empty() {
                button {
                    class: "primary",
                    disabled: s.progress.active.is_some(),
                    onclick: {
                        let questions: Vec<_> = hits.iter().take(10).map(|(_, _, q)| q.clone()).collect();
                        move |_| {
                            let questions = questions.clone();
                            spawn(async move {
                                cx.state.write().progress.active = Some(Session {
                                    id: uid().await, questions,
                                    answers: BTreeMap::new(), drafts: BTreeMap::new(), position: 0,
                                });
                                cx.page.set(Page::Session);
                            });
                        }
                    },
                    "Quiz matching questions"
                }
                if s.progress.active.is_some() {
                    p { class: "small muted", "Finish your current session before starting a search quiz." }
                }
            }
            div { class: "stack",
                for (course_title, test_title, q) in hits.iter().take(40) {
                    div { class: "panel row", key: "{q.id}",
                        div {
                            p { class: "small muted", "{course_title} · {test_title} · {q.difficulty}" }
                            strong { "{q.prompt}" }
                            if let Some(topic) = &q.topic {
                                p { class: "small muted", "Topic: {topic}" }
                            }
                        }
                        button {
                            disabled: s.progress.active.is_some(),
                            onclick: {
                                let question = q.clone();
                                move |_| {
                                    let question = question.clone();
                                    spawn(async move {
                                        cx.state.write().progress.active = Some(Session {
                                            id: uid().await, questions: vec![question],
                                            answers: BTreeMap::new(), drafts: BTreeMap::new(), position: 0,
                                        });
                                        cx.page.set(Page::Session);
                                    });
                                }
                            },
                            "Practice this question"
                        }
                    }
                }
            }
            if hits.len() > 40 {
                p { class: "small muted", "Showing the first 40 matches. Narrow your search to see more." }
            }
        }
        if let Some(catalog) = s.catalog {
            div { class: "section-head",
                h2 { "Available to download" }
            }
            div { class: "stack",
                for entry in catalog.courses.iter().filter(|e| !s.courses.iter().any(|c| c.id == e.id)) {
                    div { class: "panel row",
                        div {
                            h3 { "{entry.title}" }
                            p { class: "muted", "{entry.description}" }
                        }
                        button {
                            disabled: (cx.busy)(),
                            onclick: {
                                let entry = entry.clone();
                                move |_| {
                                    let entry = entry.clone();
                                    spawn(async move {
                                        cx.busy.set(true);
                                        let url = cx.state.read().catalog_url.clone();
                                        let result = async {
                                            let raw = call("course", json!({ "url" : url, "entry" : entry }))
                                                .await?;
                                            let course: Course = serde_json::from_str(
                                                    raw.as_str().ok_or("Invalid course response")?,
                                                )
                                                .map_err(|e| e.to_string())?;
                                            if course.id != entry.id {
                                                return Err("Course ID mismatch".into());
                                            }
                                            let mut courses = cx.state.read().courses.clone();
                                            courses.retain(|c| c.id != course.id);
                                            courses.push(course);
                                            validate_courses(&courses)?;
                                            cx.state.write().courses = courses;
                                            Ok::<_, String>(())
                                        }
                                            .await;
                                        cx.message
                                            .set(
                                                result
                                                    .err()
                                                    .unwrap_or_else(|| {
                                                        "Course downloaded for offline practice.".into()
                                                    }),
                                            );
                                        cx.busy.set(false);
                                    });
                                }
                            },
                            "Download"
                        }
                    }
                }
            }
        }
        p { class: "footer-note",
            "Original practice material · No account needed · Progress saved on this device"
        }
    }
}
#[component]
fn CourseCard(course: Course) -> Element {
    let mut cx = use_context::<AppContext>();
    let s = cx.state.read();
    let total = course
        .tests
        .iter()
        .map(|t| t.questions.len())
        .sum::<usize>();
    let answered = course
        .tests
        .iter()
        .flat_map(|t| &t.questions)
        .filter(|q| s.progress.latest(q).is_some())
        .count();
    let pct = if total == 0 {
        0
    } else {
        answered * 100 / total
    };
    let id = course.id.clone();
    rsx! {
        article { class: "card",
            div { class: "row",
                div { class: "icon",
                    if course.subject.contains("Java") {
                        "{{ }}"
                    } else if course.subject.contains("Math") {
                        "π"
                    } else {
                        "⚗"
                    }
                }
                span { class: "badge", "{course.difficulty}" }
            }
            div { class: "eyebrow", "{course.subject}" }
            h3 { "{course.title}" }
            p { "{course.description}" }
            div { class: "progress",
                span { style: "width:{pct}%" }
            }
            div { class: "row small muted",
                span { "{answered} of {total} answered" }
                span { "{pct}%" }
            }
            div { class: "card-bottom",
                span { "{course.lessons.len()} lessons · {course.tests.len()} tests" }
                button { onclick: move |_| cx.page.set(Page::Course(id.clone())), "Explore →" }
            }
        }
    }
}
#[component]
fn CourseView(id: String) -> Element {
    let mut cx = use_context::<AppContext>();
    let mut selected = use_signal(|| 0usize);
    let Some(c) = cx.state.read().courses.iter().find(|c| c.id == id).cloned() else {
        return rsx! {
            p { "Course unavailable." }
        };
    };
    let lesson = c.lessons.get(selected()).cloned();
    rsx! {
        button { class: "quiet", onclick: move |_| cx.page.set(Page::Library), "← Your library" }
        div { class: "section-head",
            div {
                div { class: "eyebrow", "{c.subject}" }
                h1 { "{c.title}" }
                p { class: "intro", "{c.description}" }
            }
        }
        div { class: "split",
            div { class: "panel",
                h3 { "Your learning path" }
                p { class: "small muted", "Follow the order or jump right in." }
                for (i, l) in c.lessons.iter().enumerate() {
                    button {
                        class: "lesson-button",
                        onclick: move |
                                _ | selected.set(i),
                        if cx.state.read().progress.lessons.contains(&l.id) {
                            "✓ "
                        } else {
                            "○ "
                        }
                        "{i+1}. {l.title}"
                    }
                }
                hr {}
                h3 { "Practice tests" }
                for t in &c.tests {
                    div { class: "results-row",
                        strong { "{t.title}" }
                        p { class: "small muted", "{t.description}" }
                        span { class: "badge",
                            {
                                let p = &cx.state.read().progress;
                                let n = t.questions.iter().filter(|q| p.latest(q).is_some()).count();
                                if n == 0 {
                                    "Not started"
                                } else if n == t.questions.len() {
                                    "Completed"
                                } else {
                                    "In progress"
                                }
                            }
                        }
                    }
                    button {
                        class: "primary",
                        onclick: move |_| cx.page.set(Page::Practice),
                        "Build a practice session"
                    }
                }
                div { class: "panel",
                    if let Some(l) = lesson {
                        h2 { "{l.title}" }
                        Markdown { text: l
                                    .markdown }
                        button {
                            class: "primary",
                            onclick: move |_| {
                                cx.state.write().progress.lessons.insert(l.id.clone());
                            },
                            "Mark lesson complete ✓"
                        }
                    } else {
                        p { "This course has no lessons yet. Try its practice questions." }
                    }
                }
            }
        }
    }
}
#[component]
fn Practice() -> Element {
    let mut cx = use_context::<AppContext>();
    let mut selected = use_signal(BTreeSet::<String>::new);
    let mut difficulty = use_signal(|| "all".to_string());
    let mut subject = use_signal(|| "all".to_string());
    let mut pool = use_signal(|| "unseen".to_string());
    let mut count = use_signal(|| "5".to_string());
    let s = (cx.state)();
    let subjects: BTreeSet<_> = s.courses.iter().map(|c| c.subject.clone()).collect();
    let mode = match pool().as_str() {
        "unanswered" => Pool::Unanswered,
        "incorrect" => Pool::Incorrect,
        "all" => Pool::All,
        _ => Pool::UnseenFirst,
    };
    let questions: Vec<_> = s
        .courses
        .iter()
        .filter(|c| subject() == "all" || subject() == c.subject)
        .flat_map(|c| &c.tests)
        .filter(|t| selected.read().contains(&t.id))
        .flat_map(|t| t.questions.iter().cloned())
        .filter(|q| difficulty() == "all" || difficulty() == q.difficulty)
        .collect();
    let available = questions
        .iter()
        .filter(|q| match mode {
            Pool::Unanswered => s.progress.latest(q).is_none(),
            Pool::Incorrect => s.progress.latest(q).is_some_and(|a| !a.correct),
            _ => true,
        })
        .count();
    rsx! {
        div { class: "eyebrow", "A LITTLE CHALLENGE GOES A LONG WAY" }
        h1 { "Make it your practice." }
        p { class: "intro",
            "Pick your tests and set a comfortable pace. Each session has unique questions, with explanations as you go."
        }
        if s.progress.active.is_some() {
            div { class: "notice",
                "You have a saved session. Finish or end it before starting another."
                button { onclick: move |_| cx.page.set(Page::Session), "Resume session" }
            }
        }
        div { class: "split",
            section { class: "panel",
                h2 { "Session settings" }
                label { class: "field",
                    "Subject"
                    select {
                        value: subject(),
                        onchange: move | e |
                                subject.set(e.value()),
                        option { value: "all", "All subjects" }
                        for name in subjects {
                            option { value: name.clone(), "{name}" }
                        }
                    }
                }
                label { class: "field",
                    "Difficulty"
                    Difficulty {
                        value: difficulty(),
                        all: true,
                        onchange: move |v| difficulty.set(v),
                    }
                }
                label { class: "field",
                    "Question selection"
                    select { value: pool(), onchange: move |e| pool.set(e.value()),
                        option { value: "unseen", "Unseen first" }
                        option { value: "unanswered", "Unanswered only" }
                        option { value: "incorrect", "Previously incorrect" }
                        option { value: "all", "All questions" }
                    }
                }
                label { class: "field",
                    "Number of questions"
                    input {
                        r#type: "number",
                        min: "1",
                        max: available
                                .to_string(),
                        value: count(),
                        oninput: move |e| count.set(e.value()),
                    }
                }
                p { class: "small muted", "{available} eligible questions" }
                button {
                    class: "primary",
                    disabled: s.progress.active.is_some() || available == 0,
                    onclick: move |_| {
                        let questions = questions.clone();
                        spawn(async move {
                            let n = count().parse().unwrap_or(0);
                            let seed = timestamp().await;
                            let selection = select_questions(questions, &cx.state.read().progress, mode, n, seed);
                            match selection {
                                Ok(qs) => {
                                    let session = Session {
                                        id: uid().await,
                                        questions: qs,
                                        answers: BTreeMap::new(),
                                        drafts: BTreeMap::new(),
                                        position: 0,
                                    };
                                    cx.state.write().progress.active = Some(session);
                                    cx.page.set(Page::Session);
                                }
                                Err(e) => cx.message.set(e),
                            }
                        });
                    },
                    "Start session →"
                }
            }
            section { class: "panel",
                h2 { "Choose your tests" }
                for c in s.courses.iter().filter(|c| subject() == "all" || subject() == c.subject) {
                    h3 { "{c.title}" }
                    for t in &c.tests {
                        label { class: "test-check",
                            input {
                                r#type: "checkbox",
                                checked: selected.read().contains(&t.id),
                                onchange: {
                                    let id = t.id.clone();
                                    move |_| {
                                        let mut set = selected.write();
                                        if !set.remove(&id) {
                                            set.insert(id.clone());
                                        }
                                    }
                                },
                            }
                            div {
                                strong { "{t.title}" }
                                span { "{t.questions.len()} questions · {t.difficulty}" }
                            }
                        }
                    }
                }
            }
        }
    }
}
#[component]
fn SessionView() -> Element {
    let mut cx = use_context::<AppContext>();
    let Some(session) = cx.state.read().progress.active.clone() else {
        return rsx! {
            div { class: "empty",
                h2 { "A fresh start awaits." }
                p { "Choose a few questions and begin your next session." }
                button {
                    class: "primary",
                    onclick: move |_| cx.page.set(Page::Practice),
                    "Set up practice"
                }
            }
        };
    };
    let q = session.questions[session.position].clone();
    rsx! {
        QuestionView {
            key: "{session.id}-{q.id}",
            question: q,
            index: session
                    .position,
            total: session.questions.len(),
        }
    }
}
#[component]
fn QuestionView(question: Question, index: usize, total: usize) -> Element {
    let mut cx = use_context::<AppContext>();
    let mut answer = use_signal(|| {
        cx.state
            .read()
            .progress
            .active
            .as_ref()
            .and_then(|s| s.drafts.get(&question.id))
            .cloned()
            .unwrap_or_else(|| initial_answer(&question))
    });
    let mut execution = use_signal(String::new);
    let mut submitting = use_signal(|| false);
    let mut end_confirm = use_signal(|| false);
    let previous = cx.state.read().progress.latest(&question).is_some();
    let submitted = cx
        .state
        .read()
        .progress
        .active
        .as_ref()
        .and_then(|s| s.answers.get(&question.id))
        .cloned();
    let submit = {
        let q = question.clone();
        move |skip: bool| {
            let q = q.clone();
            let a = if skip { Answer::Skipped } else { answer() };
            spawn(async move {
                cx.busy.set(true);
                submitting.set(true);
                let result = if let Answer::Code(source) = &a {
                    match call("java", json!({ "question" : q, "source" : source })).await {
                        Ok(result) => {
                            execution
                                .set(serde_json::to_string_pretty(&result["results"]).unwrap());
                            Ok(result["passed"] == true)
                        }
                        Err(e) => Err(e),
                    }
                } else {
                    grade(&q, &a)
                };
                match result {
                    Ok(correct) => {
                        let attempt = Attempt {
                            id: uid().await,
                            question_id: q.id.clone(),
                            revision: q.revision,
                            answer: a,
                            correct,
                            timestamp: timestamp().await,
                        };
                        let mut s = cx.state.write();
                        s.progress.attempts.push(attempt.clone());
                        if let Some(session) = &mut s.progress.active {
                            session.answers.insert(q.id.clone(), attempt);
                        }
                    }
                    Err(e) => cx.message.set(e),
                }
                cx.busy.set(false);
                submitting.set(false);
            });
        }
    };
    rsx! {
        div { class: "center",
            div { class: "question-top",
                span { class: "eyebrow", "QUESTION {index+1} OF {total}" }
                span { class: "badge", "{kind_name(&question)} · {question.difficulty}" }
            }
            div { class: "progress",
                span { style: "width:{(index+1)*100/total}%" }
            }
            section { class: "panel",
                if previous && submitted.is_none() {
                    span { class: "badge", "↻ Answered before" }
                }
                Markdown { text: question.prompt.clone() }
                AnswerFields {
                    question: question
                            .clone(),
                    answer: submitted.as_ref().map(| a | a.answer.clone())
                            .unwrap_or_else(|| answer()),
                    disabled: submitted.is_some() || submitting(),
                    onchange: {let id=question.id.clone(); move |a:Answer| {answer.set(a.clone()); if let Some(s)=&mut cx.state.write().progress.active{s.drafts.insert(id.clone(),a);}}},
                }
                if let Some(a) = submitted {
                    div { class: if a.correct { "feedback" } else { "feedback incorrect" },
                        strong {
                            if a.answer == Answer::Skipped {
                                "Skipped"
                            } else if a.correct {
                                "✓ That's correct"
                            } else {
                                "Keep learning — here's why"
                            }
                        }
                        Markdown { text: question.explanation
                                    .clone() }
                        details {
                            summary { "View answer" }
                            Markdown { text: solution(&
                                        question) }
                        }
                    }
                    if !execution().is_empty() {
                        details {
                            summary { "Test results" }
                            pre { class: "code", "{execution}" }
                        }
                    }
                    div { class: "actions",
                        button {
                            class: "primary",
                            onclick: move |_| {
                                if index + 1 < total {
                                    if let Some(s) = &mut cx.state.write().progress.active {
                                        s.position += 1;
                                    }
                                } else {
                                    cx.page.set(Page::Results);
                                }
                            },
                            if index + 1 < total {
                                "Next question →"
                            } else {
                                "View results →"
                            }
                        }
                    }
                } else {
                    div { class: "actions",
                        button {
                            class: "primary",
                            disabled: submitting(),
                            onclick: {
                                let submit = submit.clone();
                                move |_| submit(false)
                            },
                            if submitting() {
                                "Compiling & testing…"
                            } else {
                                "Check answer"
                            }
                        }
                        button {
                            disabled: submitting(),
                            onclick: move | _ |
                                    submit(true),
                            "Skip question"
                        }
                        if submitting() {
                            button {
                                onclick: move |_| {
                                    spawn(async {
                                        let _ = call("cancel", Value::Null).await;
                                    });
                                },
                                "Cancel execution"
                            }
                        }
                    }
                }
            }
            div { class: "actions",
                button {
                    class: "quiet",
                    disabled: submitting(),
                    onclick: move |_| cx.page.set(Page::Library),
                    "Save & leave"
                }
                button {
                    class: "quiet",
                    disabled: submitting(),
                    onclick: move |_| end_confirm.set(true),
                    "End session"
                }
            }
            if end_confirm() {
                div { class: "notice",
                    "End this session and review your results? Unanswered questions remain available for future practice."
                    button { onclick: move |_| cx.page.set(Page::Results), "End & review" }
                    button { onclick: move |_| end_confirm.set(false), "Keep practicing" }
                }
            }
        }
    }
}
#[component]
fn Results() -> Element {
    let mut cx = use_context::<AppContext>();
    let s = (cx.state)();
    let Some(session) = s.progress.active else {
        return rsx! {
            h1 { "Your practice history" }
            p { class: "intro", "{s.progress.attempts.len()} recorded submissions on this device." }
            div { class: "stack",
                for a in s.progress.attempts.iter().rev().take(30) {
                    div { class: "panel row",
                        span { "{a.question_id}" }
                        span { class: "badge",
                            if a.answer == Answer::Skipped {
                                "Skipped"
                            } else if a.correct {
                                "Correct"
                            } else {
                                "Incorrect"
                            }
                        }
                    }
                }
            }
        };
    };
    let correct = session.answers.values().filter(|a| a.correct).count();
    let incorrect = session
        .answers
        .values()
        .filter(|a| !a.correct && a.answer != Answer::Skipped)
        .count();
    let skipped = session.questions.len() - correct - incorrect;
    let retry: Vec<_> = session
        .questions
        .iter()
        .filter(|q| {
            session
                .answers
                .get(&q.id)
                .is_some_and(|a| !a.correct && a.answer != Answer::Skipped)
        })
        .cloned()
        .collect();
    rsx! {
        div { class: "eyebrow", "PROGRESS, ONE QUESTION AT A TIME" }
        h1 { "Every attempt counts." }
        p { class: "intro", "Review what clicked, revisit what didn’t, and keep going." }
        div { class: "stats",
            div { class: "stat",
                strong { "{correct}" }
                span { "correct" }
            }
            div { class: "stat",
                strong { "{incorrect}" }
                span { "incorrect" }
            }
            div { class: "stat",
                strong { "{skipped}" }
                span { "skipped / unanswered" }
            }
        }
        div { class: "panel",
            for q in &session.questions {
                details { class: "results-row",
                    summary {
                        "{q.prompt}"
                        span { class: "badge",
                            {
                                match session.answers.get(&q.id) {
                                    Some(a) if a.correct => "Correct",
                                    Some(a) if a.answer != Answer::Skipped => "Incorrect",
                                    _ => "Skipped",
                                }
                            }
                        }
                        Markdown { text: q.explanation.clone() }
                        Markdown { text: solution(q) }
                    }
                }
            }
            div { class: "actions",
                button {
                    class: "primary",
                    disabled: retry.is_empty(),
                    onclick: move |_| {
                        let retry = retry.clone();
                        spawn(async move {
                            cx.state.write().progress.active = Some(Session {
                                id: uid().await,
                                questions: retry,
                                answers: BTreeMap::new(),
                                        drafts: BTreeMap::new(),
                                position: 0,
                            });
                            cx.page.set(Page::Session);
                        });
                    },
                    "Retry incorrect"
                }
                button {
                    onclick: move |_| {
                        cx.state.write().progress.active = None;
                        cx.page.set(Page::Practice);
                    },
                    "Finish session"
                }
            }
        }
    }
}
#[component]
fn Settings() -> Element {
    let mut cx = use_context::<AppContext>();
    let mut url = use_signal(|| cx.state.read().catalog_url.clone());
    let mut pack_url = use_signal(|| cx.state.read().pack_url.clone());
    let mut confirm = use_signal(|| false);
    rsx! {
        h1 { "Make yourself at home." }
        p { class: "intro",
            "Connect your content, prepare for offline practice, and take your progress with you."
        }
        div { class: "stack",
            section { class: "panel",
                h2 { "Course repository" }
                p { class: "small muted",
                    "Use the raw HTTPS URL of a public catalog.json. Switching collections starts a separate history; export your current backup first."
                }
                label { class: "field",
                    "Catalog URL"
                    input {
                        r#type: "url",
                        value: url(),
                        placeholder: "https://raw.githubusercontent.com/you/repo/main/catalog.json",
                        oninput: move |e| url.set(e.value()),
                    }
                }
                button {
                    class: "primary",
                    disabled: (cx.busy)() || (cx.syncing)(),
                    onclick: move |_| {
                        spawn(async move {
                            cx.syncing.set(true);
                            cx.sync_status.set("Checking for question updates…".into());
                            let result = sync_catalog(cx, url(), false).await;
                            match result {
                                Ok(status) => cx.sync_status.set(status),
                                Err(e) if e.contains("different collection") => {
                                    confirm.set(true);
                                    cx.sync_status.set(e);
                                }
                                Err(e) => cx.sync_status.set(format!("Using cached questions: {e}")),
                            }
                            cx.syncing.set(false);
                        });
                    },
                    "Sync questions now"
                }
                if let Some(last) = cx.state.read().last_synced.as_ref() {
                    p { class: "small muted", "Last successful sync: {last}" }
                }
                if !(cx.sync_status)().is_empty() {
                    p { role: "status", "{(cx.sync_status)()}" }
                }
                if confirm() {
                    div { class: "notice",
                        "This is a different collection. Switching will replace the current library and progress. Export a backup first if you need it."
                        button {
                            onclick: move |_| {
                                confirm.set(false);
                                spawn(async move {
                                    cx.syncing.set(true);
                                    cx.sync_status.set("Switching collection…".into());
                                    let result = sync_catalog(cx, url(), true).await;
                                    cx.sync_status.set(result.unwrap_or_else(|e| format!("Using cached questions: {e}")));
                                    cx.syncing.set(false);
                                });
                            },
                            "Switch and sync"
                        }
                        button { onclick: move | _
                                    | confirm.set(false), "Cancel" }
                    }
                }
            }
            section { class: "panel",
                h2 { "Offline Java pack" }
                p { class: "small muted",
                    "A separate ~6.4 MB download. Supports basic Java programs, methods, collections, and a small Scanner adapter. Advanced JVM APIs and external dependencies are unsupported."
                }
                p { class: "badge",
                    if (cx.pack)() {
                        "✓ Pack installed"
                    } else {
                        "Not installed"
                    }
                }
                label { class: "field",
                    "Java pack directory URL"
                    input {
                        value: pack_url(),
                        placeholder: "https://your-site.example/java-pack/",
                        oninput: move |e| pack_url.set(e.value()),
                    }
                }
                button {
                    class: "primary",
                    disabled: (cx.busy)(),
                    onclick: move |_| {
                        spawn(async move {
                            cx.busy.set(true);
                            cx.message.set("Downloading and verifying Java pack…".into());
                            match call("installPack", json!(pack_url())).await {
                                Ok(_) => {
                                    cx.pack.set(true);
                                    cx.state.write().pack_url = pack_url();
                                    cx.message
                                        .set(
                                            "Java pack installed. Code practice is ready offline.".into(),
                                        );
                                }
                                Err(e) => cx.message.set(e),
                            }
                            cx.busy.set(false);
                        });
                    },
                    "Download / verify pack"
                }
            }
            section { class: "panel",
                h2 { "Your progress, anywhere" }
                p { class: "small muted",
                    "Export a backup on one device and import it on another. Repeated imports do not duplicate attempts; this device’s active session takes priority."
                }
                div { class: "actions",
                    button {
                        onclick: move |_| {
                            let text = serde_json::to_string_pretty(&cx.state.read().progress).unwrap();
                            spawn(async move {
                                if let Err(e) = call(
                                        "download",
                                        json!({ "name" : "tutorialz-progress.json", "text" : text }),
                                    )
                                    .await
                                {
                                    cx.message.set(e);
                                }
                            });
                        },
                        "Export progress"
                    }
                    button {
                        onclick: move |_| {
                            spawn(async move {
                                let result = async {
                                    let raw = call("pick", Value::Null).await?;
                                    if raw.is_null() {
                                        return Ok(());
                                    }
                                    let p: Progress = serde_json::from_str(
                                            raw.as_str().ok_or("Invalid file")?,
                                        )
                                        .map_err(|e| e.to_string())?;
                                    cx.state.write().progress.merge(p)
                                }
                                    .await;
                                cx.message
                                    .set(result.err().unwrap_or_else(|| "Progress import complete.".into()));
                            });
                        },
                        "Import progress"
                    }
                }
            }
        }
    }
}
