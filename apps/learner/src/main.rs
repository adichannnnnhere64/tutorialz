use dioxus::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use tutorialz_core::*;
use tutorialz_ui::*;
mod study;
const DEFAULT_CATALOG_URL: &str = "https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json";
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
                .unwrap_or(DEFAULT_CATALOG_URL)
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
impl State {
    fn upgrade_bundled_content(&mut self) {
        let bundled = Self::default();
        // Only upgrade the default source. Custom catalogs remain under the user's control.
        if self.catalog_url == DEFAULT_CATALOG_URL
            && self.progress.collection_id == bundled.progress.collection_id
            && self.catalog.as_ref().is_none_or(|current| {
                current.content_revision < bundled.catalog.as_ref().unwrap().content_revision
            })
        {
            self.catalog = bundled.catalog;
            self.courses = bundled.courses;
            self.last_synced = None;
            // Attempts and the active session retain their original question snapshots.
        }
    }
}
#[derive(Clone, PartialEq)]
enum Page {
    Library,
    Course(String),
    Practice,
    PracticeTest(String),
    Session,
    Results,
    Settings,
    Study,
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
    if let Some(current) = &original.catalog {
        validate_catalog_update(current, &catalog)?;
    }
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
    let mut page = use_signal(|| Page::Library);
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
                        Ok(mut s) => {
                            if validate_courses(&s.courses).is_ok() && s.progress.validate().is_ok()
                            {
                                s.upgrade_bundled_content();
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
    let learn_active = matches!(&current, Page::Library | Page::Course(_));
    let practice_active = matches!(&current, Page::Practice | Page::PracticeTest(_));
    let activity_active = matches!(&current, Page::Session | Page::Results);
    let settings_active = matches!(&current, Page::Settings);
    let mobile_title = match &current {
        Page::Library => "Learn",
        Page::Course(_) => "Course",
        Page::Practice | Page::PracticeTest(_) => "Practice",
        Page::Session => "Session",
        Page::Results => "Activity",
        Page::Settings => "Settings",
        Page::Study => "Study",
    };
    let screen_class = match &current {
        Page::Library => "screen-library",
        Page::Course(_) => "screen-course",
        Page::Practice | Page::PracticeTest(_) => "screen-practice",
        Page::Session => "screen-session",
        Page::Results => "screen-results",
        Page::Settings => "screen-settings",
        Page::Study => "screen-study",
    };
    let shell_class = match (cfg!(target_os = "android"), &current) {
        (true, Page::Session) => "shell learner-shell native-android in-session",
        (true, _) => "shell learner-shell native-android",
        (false, Page::Session) => "shell learner-shell in-session",
        (false, _) => "shell learner-shell",
    };
    rsx! {
        style { dangerous_inner_html: CSS }
        if study::AVAILABLE {
            style { dangerous_inner_html: study::CSS }
        }
        div { class: shell_class,
            aside { class: "sidebar",
                div { class: "brand",
                    span { class: "brand-mark", "t" }
                    "tutorialz"
                }
                Nav { label: "▦  My learning", target: Page::Library }
                if study::AVAILABLE {
                    Nav { label: "▤  Study syllabus", target: Page::Study }
                }
                Nav { label: "✓  Practice", target: Page::Practice }
                Nav {
                    label: "◷  Session & results",
                    target: match state.read().progress.active.as_ref() {
                        Some(session) if !session.fast_mode || session.answers.is_empty() => Page::Session,
                        _ => Page::Results,
                    },
                }
                Nav { label: "⚙  Settings & backups", target: Page::Settings }
                div { class: "bottom",
                    "A little practice, every day."
                    br {}
                    "Your progress stays with you."
                }
            }
            main { class: "main {screen_class}",
                header { class: "mobile-header",
                    div { class: "mobile-toolbar",
                        if matches!(&current, Page::Course(_) | Page::Session) {
                            button {
                                class: "mobile-back",
                                onclick: move |_| page.set(Page::Library),
                                "‹  Learn"
                            }
                        } else {
                            span { class: "mobile-wordmark", "tutorialz" }
                        }
                        span { class: "mobile-header-caption", "ON THIS DEVICE" }
                    }
                    h1 { class: "mobile-page-title", "{mobile_title}" }
                }
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
                            Practice { preset: None }
                        },
                        Page::PracticeTest(id) => rsx! {
                            Practice { preset: Some(id) }
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
                        Page::Study => rsx! { study::Study {} },
                    }
                }
            }
            nav { class: "mobile-tabbar", aria_label: "Learner navigation",
                MobileTab {
                    label: "Learn",
                    icon: "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
                    target: Page::Library,
                    active: learn_active,
                }
                MobileTab {
                    label: "Practice",
                    icon: "M12 3a9 9 0 1 0 9 9M12 3a9 9 0 0 1 9 9M8 12l2.5 2.5L16 9",
                    target: Page::Practice,
                    active: practice_active,
                }
                if study::AVAILABLE {
                    MobileTab {
                        label: "Study",
                        icon: "M3 4h6l3 2 3-2h6v16h-6l-3 2-3-2H3zM12 6v16",
                        target: Page::Study,
                        active: matches!((cx.page)(), Page::Study),
                    }
                }
                MobileTab {
                    label: "Activity",
                    icon: "M3 20h18M5 16l4-5 4 3 6-8M16 6h3v3",
                    target: match state.read().progress.active.as_ref() {
                        Some(session) if !session.fast_mode || session.answers.is_empty() => Page::Session,
                        _ => Page::Results,
                    },
                    active: activity_active,
                }
                MobileTab {
                    label: "Settings",
                    icon: "M4 7h16M4 17h16M9 4v6M15 14v6",
                    target: Page::Settings,
                    active: settings_active,
                }
            }
        }
    }
}
#[component]
fn Nav(label: String, target: Page) -> Element {
    let mut cx = use_context::<AppContext>();
    let current = (cx.page)();
    let active =
        current == target || matches!((&target, &current), (Page::Practice, Page::PracticeTest(_)));
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
fn MobileTab(label: String, icon: String, target: Page, active: bool) -> Element {
    let mut cx = use_context::<AppContext>();
    rsx! {
        button {
            class: if active { "mobile-tab active" } else { "mobile-tab" },
            aria_label: "{label}",
            onclick: move |_| {
                if !(cx.busy)() {
                    cx.page.set(target.clone());
                    cx.message.set(String::new());
                }
            },
            svg {
                view_box: "0 0 24 24",
                fill: "none",
                stroke: "currentColor",
                stroke_width: "1.8",
                stroke_linecap: "round",
                stroke_linejoin: "round",
                path { d: "{icon}" }
            }
            span { "{label}" }
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
    let has_active_session = s.progress.active.is_some();
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
                    "{} {} {} {} {} {}",
                    c.title,
                    t.title,
                    q.prompt,
                    q.topic.as_deref().unwrap_or(""),
                    q.second_topic.as_deref().unwrap_or(""),
                    q.assessment
                        .as_ref()
                        .map(|a| a.concepts.join(" ").replace('-', " "))
                        .unwrap_or_default()
                )
                .to_lowercase();
                terms.iter().all(|word| haystack.contains(word))
            })
            .map(|(c, t, q)| (c.title.clone(), t.title.clone(), q.clone()))
            .collect()
    };
    rsx! {
        section { class: "mobile-dashboard",
            span { class: "mobile-dashboard-label", "TODAY'S MOMENTUM" }
            strong { "A little progress adds up." }
            p { "{answered} answered · {correct} correct on your latest tries" }
            button {
                class: "primary",
                onclick: move |_| cx.page.set(if has_active_session { Page::Session } else { Page::Practice }),
                if has_active_session { "Continue session" } else { "Start practice" }
                span { "→" }
            }
        }
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
        div { class: "mobile-list-heading",
            h2 { "Your courses" }
            span { "{s.courses.len()} available" }
        }
        div { class: "section-head library-section-head",
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
                                    answers: BTreeMap::new(), drafts: BTreeMap::new(), fast_mode: false, position: 0,
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
                            Markdown { text: q.prompt.clone() }
                            QuestionSource { question: q.clone() }
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
                                            answers: BTreeMap::new(), drafts: BTreeMap::new(), fast_mode: false, position: 0,
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
        button {
            class: "mobile-course-row",
            aria_label: "Open {course.title}",
            onclick: {
                let id = id.clone();
                move |_| cx.page.set(Page::Course(id.clone()))
            },
            span { class: "mobile-course-symbol",
                if course.subject.contains("Java") { "{{ }}" } else { "✦" }
            }
            span { class: "mobile-course-content",
                strong { "{course.title}" }
                small { "{course.subject} · {answered} of {total} answered" }
                span { class: "mobile-course-progress",
                    span { style: "width:{pct}%" }
                }
            }
            span { class: "mobile-chevron", "›" }
        }
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
        div { class: "course-layout",
            div { class: if c.lessons.is_empty() { "panel course-path no-lessons" } else { "panel course-path" },
                h3 { "Your learning path" }
                p { class: "small muted",
                    if c.lessons.is_empty() {
                        "Choose a practice test to build a session."
                    } else {
                        "Follow the order or jump right in."
                    }
                }
                if !c.lessons.is_empty() {
                    div { class: "lesson-list",
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
                    }
                }
                hr {}
                h3 { "Practice tests" }
                div { class: "practice-test-list",
                    for t in &c.tests {
                        button {
                            class: "mobile-test-row",
                            onclick: {
                                let id = t.id.clone();
                                move |_| cx.page.set(Page::PracticeTest(id.clone()))
                            },
                            span { class: "mobile-test-icon", "✓" }
                            span { class: "mobile-test-content",
                                strong { "{t.title}" }
                                small { "{t.questions.len()} questions · {t.difficulty}" }
                            }
                            span { class: "mobile-chevron", "›" }
                        }
                        div { class: "practice-test",
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
                            button {
                                class: "primary",
                                onclick: {
                                    let id = t.id.clone();
                                    move |_| cx.page.set(Page::PracticeTest(id.clone()))
                                },
                                "Build a practice session"
                            }
                        }
                    }
                }
            }
            if let Some(l) = lesson {
                div { class: "panel",
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
                }
            }
        }
    }
}
#[component]
fn Practice(preset: Option<String>) -> Element {
    let mut cx = use_context::<AppContext>();
    let mut selected = use_signal(move || preset.into_iter().collect::<BTreeSet<String>>());
    let mut difficulty = use_signal(|| "all".to_string());
    let mut subject = use_signal(|| "all".to_string());
    let mut pool = use_signal(|| "unseen".to_string());
    let mut count = use_signal(|| "5".to_string());
    let mut fast_mode = use_signal(|| false);
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
    let fast_results_ready = s
        .progress
        .active
        .as_ref()
        .is_some_and(|session| session.fast_mode && !session.answers.is_empty());
    rsx! {
        div { class: "eyebrow", "A LITTLE CHALLENGE GOES A LONG WAY" }
        h1 { "Make it your practice." }
        p { class: "intro",
            "Pick your tests and set a comfortable pace. Each session has unique questions, with explanations to review."
        }
        if s.progress.active.is_some() {
            div { class: "notice",
                "You have a saved session. Finish or end it before starting another."
                button {
                    onclick: move |_| cx.page.set(if fast_results_ready { Page::Results } else { Page::Session }),
                    if fast_results_ready { "View results" } else { "Resume session" }
                }
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
                label { class: "test-check",
                    input {
                        r#type: "checkbox",
                        checked: fast_mode(),
                        onchange: move |_| fast_mode.set(!fast_mode()),
                    }
                    div {
                        strong { "Fast mode" }
                        span { "Single-choice answers move to the next question immediately. Review results after finishing." }
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
                                        fast_mode: fast_mode(),
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
                p { class: "mobile-picker-help", "Select a course, then choose the tests you want to practice." }
                div { class: "mobile-test-picker",
                    for c in s.courses.iter().filter(|c| subject() == "all" || subject() == c.subject) {
                        details { class: "mobile-test-group",
                            summary {
                                span {
                                    strong { "{c.title}" }
                                    small { "{c.tests.len()} tests" }
                                }
                                span { class: "mobile-chevron", "›" }
                            }
                            div { class: "mobile-test-options",
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
                div { class: "desktop-test-picker",
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
    if session.fast_mode && !session.answers.is_empty() {
        return rsx! { Results {} };
    }
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
    let fast_mode = cx
        .state
        .read()
        .progress
        .active
        .as_ref()
        .is_some_and(|s| s.fast_mode);
    let auto_advance = matches!(
        question.kind,
        QuestionKind::Choice {
            multiple: false,
            ..
        }
    );
    let answer = cx
        .state
        .read()
        .progress
        .active
        .as_ref()
        .and_then(|s| s.drafts.get(&question.id))
        .cloned()
        .unwrap_or_else(|| initial_answer(&question));
    let has_fast_answer = cx
        .state
        .read()
        .progress
        .active
        .as_ref()
        .is_some_and(|s| s.drafts.contains_key(&question.id));
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
            let a = if skip {
                Answer::Skipped
            } else {
                cx.state
                    .read()
                    .progress
                    .active
                    .as_ref()
                    .and_then(|s| s.drafts.get(&q.id))
                    .cloned()
                    .unwrap_or_else(|| initial_answer(&q))
            };
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
                            session.drafts.remove(&q.id);
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
                QuestionSource { question: question.clone() }
                AnswerFields {
                    question: question
                            .clone(),
                    answer: submitted.as_ref().map(|attempt| {
                        if matches!(question.kind, QuestionKind::Choice { .. }) {
                            initial_answer(&question)
                        } else {
                            attempt.answer.clone()
                        }
                    }).unwrap_or_else(|| answer.clone()),
                    disabled: submitted.is_some() || submitting() || (cx.busy)(),
                    onchange: {let id=question.id.clone(); move |a:Answer| {
                        if let Some(s)=&mut cx.state.write().progress.active {
                            s.drafts.insert(id.clone(),a);
                        }
                        if fast_mode && auto_advance && index + 1 < total {
                            spawn(async move {
                                let _ = call("nextTurn", Value::Null).await;
                                if let Some(s)=&mut cx.state.write().progress.active {
                                    if s.position == index { s.position += 1; }
                                }
                            });
                        }
                    }},
                }
                if fast_mode {
                    p { class: "small muted",
                        if auto_advance {
                            "Choose an answer to move on, or use Next to skip."
                        } else {
                            "Choose your answers, then use Next to continue."
                        }
                    }
                    div { class: "actions",
                        if index + 1 < total {
                            button {
                                class: "primary",
                                disabled: (cx.busy)(),
                                onclick: move |_| {
                                    if let Some(s) = &mut cx.state.write().progress.active {
                                        s.position += 1;
                                    }
                                },
                                "Next question →"
                            }
                        } else {
                            button {
                                class: "primary",
                                disabled: (cx.busy)() || !has_fast_answer,
                                onclick: move |_| {
                                    cx.busy.set(true);
                                    spawn(async move { finish_fast_session(cx).await; });
                                },
                                if (cx.busy)() { "Finishing…" } else { "Finish exam →" }
                            }
                            if !has_fast_answer {
                                button {
                                    disabled: (cx.busy)(),
                                    onclick: move |_| {
                                        cx.busy.set(true);
                                        spawn(async move { finish_fast_session(cx).await; });
                                    },
                                    "Skip & finish"
                                }
                            }
                        }
                    }
                } else if let Some(a) = submitted {
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
                        SubmittedAnswer { question: question.clone(), answer: Some(a.answer.clone()) }
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
                if index > 0 {
                    button {
                        class: "quiet",
                        disabled: submitting() || (cx.busy)(),
                        onclick: move |_| {
                            if let Some(s) = &mut cx.state.write().progress.active {
                                s.position -= 1;
                            }
                        },
                        "← Previous question"
                    }
                }
                button {
                    class: "quiet",
                    disabled: submitting() || (cx.busy)(),
                    onclick: move |_| cx.page.set(Page::Library),
                    "Save & leave"
                }
                button {
                    class: "quiet",
                    disabled: submitting() || (cx.busy)(),
                    onclick: move |_| end_confirm.set(true),
                    "End session"
                }
            }
            if end_confirm() {
                div { class: "notice",
                    "End this session and review your results? Unanswered questions remain available for future practice."
                    button { onclick: move |_| {
                        if fast_mode {
                            cx.busy.set(true);
                            spawn(async move { finish_fast_session(cx).await; });
                        } else {
                            cx.page.set(Page::Results);
                        }
                    }, "End & review" }
                    button { onclick: move |_| end_confirm.set(false), "Keep practicing" }
                }
            }
        }
    }
}
async fn finish_fast_session(mut cx: AppContext) {
    let Some(session) = cx.state.read().progress.active.clone() else {
        cx.busy.set(false);
        return;
    };
    if !session.fast_mode || !session.answers.is_empty() {
        cx.busy.set(false);
        return;
    }
    let mut attempts = Vec::with_capacity(session.questions.len());
    for question in &session.questions {
        let answer = session
            .drafts
            .get(&question.id)
            .cloned()
            .unwrap_or(Answer::Skipped);
        let result = if let Answer::Code(source) = &answer {
            call("java", json!({ "question": question, "source": source }))
                .await
                .map(|result| result["passed"] == true)
        } else {
            grade(question, &answer)
        };
        let correct = match result {
            Ok(correct) => correct,
            Err(error) => {
                cx.message.set(error);
                cx.busy.set(false);
                return;
            }
        };
        attempts.push(Attempt {
            id: uid().await,
            question_id: question.id.clone(),
            revision: question.revision,
            answer,
            correct,
            timestamp: timestamp().await,
        });
    }
    {
        let mut state = cx.state.write();
        if state
            .progress
            .active
            .as_ref()
            .is_some_and(|s| s.id == session.id)
        {
            state.progress.attempts.extend(attempts.iter().cloned());
            if let Some(active) = &mut state.progress.active {
                for attempt in attempts {
                    active.answers.insert(attempt.question_id.clone(), attempt);
                }
                active.drafts.clear();
            }
        }
    }
    cx.busy.set(false);
    cx.page.set(Page::Results);
}
#[component]
fn Results() -> Element {
    let mut cx = use_context::<AppContext>();
    let s = (cx.state)();
    let Some(session) = s.progress.active else {
        return rsx! {
            h1 { "Your practice history" }
            p { class: "intro", "{s.progress.attempts.len()} recorded submissions on this device." }
            if s.progress.attempts.is_empty() {
                div { class: "panel activity-empty",
                    span { class: "activity-empty-icon", "✓" }
                    h2 { "Your first session starts here" }
                    p { "Practice a few questions and your progress will appear here." }
                    button {
                        class: "primary",
                        onclick: move |_| cx.page.set(Page::Practice),
                        "Start practicing"
                    }
                }
            } else {
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
                        span {
                            if q.prompt.contains("```java") {
                                {q.topic.as_deref().map(question_topic_label).unwrap_or("Code reasoning")}
                            } else {
                                "{q.prompt.lines().next().unwrap_or(&q.prompt)}"
                            }
                        }
                        span { class: "badge",
                            {
                                match session.answers.get(&q.id) {
                                    Some(a) if a.correct => "Correct",
                                    Some(a) if a.answer != Answer::Skipped => "Incorrect",
                                    _ => "Skipped",
                                }
                            }
                        }
                    }
                    Markdown { text: q.prompt.clone() }
                    QuestionSource { question: q.clone() }
                    div { class: if session.answers.get(&q.id).is_some_and(|a| a.correct) { "answer-review" } else { "answer-review incorrect" },
                        SubmittedAnswer {
                            question: q.clone(),
                            answer: session.answers.get(&q.id).map(|a| a.answer.clone())
                        }
                    }
                    strong { "Correct answer" }
                    Markdown { text: solution(q) }
                    strong { "Explanation" }
                    Markdown { text: q.explanation.clone() }
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
                                fast_mode: session.fast_mode,
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
