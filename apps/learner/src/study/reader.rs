use crate::AppContext;
use dioxus::prelude::*;
use tutorialz_ui::Markdown;
#[path = "content.rs"]
mod content;
use content::TOPICS;

fn top() {
    document::eval("window.scrollTo(0,0)");
}

fn navigate(
    mut cx: AppContext,
    mut selected: Signal<Option<usize>>,
    mut section: Signal<usize>,
    topic: usize,
    part: usize,
    sub: Option<usize>,
) {
    let sections = TOPICS[topic].sections();
    let part = part.min(sections.len().saturating_sub(1));
    selected.set(Some(topic));
    section.set(part);
    cx.state
        .write()
        .progress
        .study
        .visit(TOPICS[topic].id, &sections[part].id);
    if let Some(sub) = sub {
        document::eval(&format!("requestAnimationFrame(() => document.getElementById('study-{topic}-{part}-{sub}')?.scrollIntoView({{block:'start'}}))"));
    } else {
        top();
    }
}

#[component]
pub fn Study() -> Element {
    let mut cx = use_context::<AppContext>();
    let mut selected = use_signal(|| None::<usize>);
    let section = use_signal(|| 0usize);
    let mut query = use_signal(String::new);
    let mut filter = use_signal(|| "all".to_owned());
    let progress = cx.state.read().progress.study.clone();
    let completed = TOPICS
        .iter()
        .filter(|topic| progress.read.contains(topic.id))
        .count();
    let resume = progress
        .last_topic
        .as_ref()
        .and_then(|id| TOPICS.iter().position(|t| t.id == id));
    let resume_section = resume
        .map(|index| TOPICS[index].resume(&progress))
        .unwrap_or(0);
    let hits: Vec<usize> = TOPICS
        .iter()
        .enumerate()
        .filter(|(_, topic)| {
            topic.matches(&query())
                && match filter().as_str() {
                    "saved" => progress.bookmarks.contains(topic.id),
                    "unread" => !progress.read.contains(topic.id),
                    _ => true,
                }
        })
        .map(|(index, _)| index)
        .collect();
    rsx! {
        div { class: "study-view",
            if let Some(index) = selected() {
                {
                    let topic = &TOPICS[index];
                    let sections = topic.sections();
                    let current = section().min(sections.len().saturating_sub(1));
                    let active = &sections[current];
                    let saved = progress.bookmarks.contains(topic.id);
                    let read = progress.read.contains(topic.id);
                    rsx! {
                        button { class: "quiet study-back", onclick: move |_| { selected.set(None); top(); }, "‹ All topics" }
                        div { class: "study-topic-heading",
                            span { class: "study-kicker", "{topic.group}" }
                            h2 { "{topic.title}" }
                            p { "{topic.summary}" }
                            button {
                                class: "study-bookmark", aria_pressed: saved,
                                onclick: move |_| {
                                    let mut state = cx.state.write();
                                    if !state.progress.study.bookmarks.remove(topic.id) {
                                        state.progress.study.bookmarks.insert(topic.id.into());
                                    }
                                },
                                if saved { "★ Saved" } else { "☆ Save topic" }
                            }
                        }
                        nav { class: "study-sections", aria_label: "Topic sections",
                            for (position, part) in sections.iter().enumerate() {
                                button {
                                    key: "{topic.id}-{position}",
                                    class: if current == position { "selected" } else { "" },
                                    aria_current: if current == position { "step" } else { "false" },
                                    onclick: move |_| {
                                        navigate(cx, selected, section, index, position, None);
                                    },
                                    "{part.title}"
                                }
                            }
                        }
                        details { class: "study-outline",
                            summary { "Chapter contents · find a subtopic" }
                            nav { aria_label: "Chapter contents",
                                for (position, part) in sections.iter().enumerate() {
                                    div { class: "study-outline-section",
                                        button { onclick: move |_| navigate(cx, selected, section, index, position, None), "{part.title}" }
                                        for (sub, (title, _)) in part.subtopics().iter().enumerate() {
                                            button { class: "study-subtopic", onclick: move |_| navigate(cx, selected, section, index, position, Some(sub)), "{title}" }
                                        }
                                    }
                                }
                            }
                        }
                        article { class: "study-article", aria_label: "Study lesson",
                            p { class: "study-kicker", "Section {current + 1} of {sections.len()} · Available offline" }
                            h3 { "{active.title}" }
                            Markdown { text: active.introduction().to_string() }
                            for (sub, (title, body)) in active.subtopics().iter().enumerate() {
                                section { class: "study-subsection", id: "study-{index}-{current}-{sub}",
                                    h4 { "{title}" }
                                    Markdown { text: body.to_string() }
                                }
                            }
                        }
                        div { class: "study-paging",
                            button { disabled: current == 0, onclick: move |_| {
                                navigate(cx, selected, section, index, current.saturating_sub(1), None);
                            }, "← Previous section" }
                            if current + 1 < sections.len() {
                                button { class: "primary", onclick: move |_| {
                                    navigate(cx, selected, section, index, current + 1, None);
                                }, "Next section →" }
                            }
                        }
                        button { class: "study-complete", aria_pressed: read, onclick: move |_| {
                            let mut state = cx.state.write();
                            if !state.progress.study.read.remove(topic.id) {
                                state.progress.study.read.insert(topic.id.into());
                            }
                        }, if read { "✓ Topic read — mark unread" } else { "Mark topic as read" } }
                        if index + 1 < TOPICS.len() {
                            button { class: "study-next", onclick: move |_| {
                                navigate(cx, selected, section, index + 1, 0, None);
                            }, "Next topic: {TOPICS[index + 1].title} →" }
                        }
                    }
                }
            } else {
                section { class: "study-intro",
                    span { class: "study-kicker", "YOUR JAVA & JAKARTA SYLLABUS" }
                    h2 { "Understand it. Then practise it." }
                    p { "24 full study chapters: foundations, worked examples, advanced concepts, production scenarios and exam reasoning. Every lesson is on your device." }
                    p { class: "study-progress", "{completed} of {TOPICS.len()} topics read" }
                    progress { value: "{completed}", max: "{TOPICS.len()}", aria_label: "Study reading progress" }
                    if let Some(index) = resume {
                        button { class: "primary", onclick: move |_| {
                            navigate(cx, selected, section, index, resume_section, None);
                        }, "Continue: {TOPICS[index].title}" }
                    }
                }
                label { class: "study-search", "Find a topic or concept",
                    input { r#type: "search", placeholder: "Hibernate, JMS, Java 9, transactions…", value: "{query}",
                        oninput: move |event| query.set(event.value()) }
                }
                div { class: "study-filters", role: "group", aria_label: "Filter study topics",
                    for (value, label) in [("all", "All topics"), ("saved", "Saved"), ("unread", "Unread")] {
                        button { aria_pressed: filter() == value,
                            class: if filter() == value { "selected" } else { "" },
                            onclick: move |_| filter.set(value.into()), "{label}" }
                    }
                }
                nav { class: "study-markers", aria_label: "Topic markers",
                    for index in hits.iter().copied() {
                        button { key: "marker-{TOPICS[index].id}", onclick: move |_| {
                            navigate(cx, selected, section, index, 0, None);
                        }, "{TOPICS[index].title}" }
                    }
                }
                p { class: "study-count", role: "status", "{hits.len()} topics found" }
                if hits.is_empty() {
                    p { class: "notice", "No topics match. Try another keyword, or select All topics." }
                }
                div { class: "study-topics",
                    for index in hits {
                        div { class: "study-topic-result", key: "topic-{TOPICS[index].id}",
                        button { class: "study-topic-card", onclick: move |_| {
                            navigate(cx, selected, section, index, 0, None);
                        },
                            span { class: "study-kicker", "{TOPICS[index].group}" }
                            strong { "{TOPICS[index].title}" }
                            span { "{TOPICS[index].summary}" }
                            small {
                                if progress.read.contains(TOPICS[index].id) { "✓ Read · " }
                                if progress.bookmarks.contains(TOPICS[index].id) { "★ Saved · " }
                                "{TOPICS[index].sections().len()} sections →"
                            }
                        }
                        if !query().trim().is_empty() {
                            div { class: "study-search-matches", aria_label: "Matching sections in {TOPICS[index].title}",
                                for (part, sub, label) in TOPICS[index].search_sections(&query()) {
                                    button { onclick: move |_| navigate(cx, selected, section, index, part, sub), "{label} →" }
                                }
                            }
                        }
                        }
                    }
                }
                details { class: "study-sources",
                    summary { "Syllabus scope & further reading" }
                    p { "Covers the original Jakarta Competency and Dummy Exam topic lists: implementation, architecture, deployment, tools and modernization. Start with Java foundations, then frameworks and messaging. The examples use Java 17 unless Java 8, 9 or 21 is named. Framework fragments need their stated libraries; the notes explain the relevant behavior." }
                    p { "Independent learning material, not an official Accenture syllabus or a reproduction of its assessments. Each chapter separates exam reasoning from production guidance and identifies its version baseline and source-review date. External references require internet; the lessons themselves work offline. Older cheatsheets may use javax packages or historical server versions." }
                    a { href: "https://cs2113f18.github.io/java/JavaCheatSheet.pdf", target: "_blank", rel: "noopener noreferrer", "Java language cheatsheet (PDF)" }
                    a { href: "https://introcs.cs.princeton.edu/java/11cheatsheet/", target: "_blank", rel: "noopener noreferrer", "Princeton Java cheatsheet" }
                    a { href: "https://it-cheat-sheets-21aa0a.gitlab.io/java-cheat-sheet.html", target: "_blank", rel: "noopener noreferrer", "IT Cheat Sheets: Java" }
                    a { href: "https://rieckpil.de/cheatsheet-java-jakarta-ee-application-servers/", target: "_blank", rel: "noopener noreferrer", "Rieckpil application server overview" }
                }
            }
        }
    }
}
