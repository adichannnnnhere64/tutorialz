use dioxus::prelude::*;
use serde_json::{json, Value};
use tutorialz_core::*;
pub const CSS: &str = include_str!("../../../public/style.css");
pub async fn init() -> Result<(), String> {
    let runner = include_str!("../../../public/java-runner.js")
        .replace("export function", "function")
        .replace("export async function", "async function");
    let code = format!(
        "{runner}\nwindow.tutorialzRunJava=runJava;\n{}\ndioxus.send(true);",
        include_str!("../../../public/bridge.js"),
    );
    document::eval(&code)
        .recv::<bool>()
        .await
        .map_err(|e| e.to_string())?;
    call(
        "configure",
        json!(
            { "worker" : include_str!("../../../public/java-worker.js"), "manifest" :
            serde_json::from_str::< Value >
            (include_str!("../../../public/java-pack/manifest.json")).unwrap() }
        ),
    )
    .await?;
    Ok(())
}
pub async fn call(method: &str, args: Value) -> Result<Value, String> {
    #[cfg(target_os = "android")]
    if method == "download" {
        android_export(
            args["name"].as_str().ok_or("Missing filename")?,
            args["text"].as_str().ok_or("Missing content")?,
        )?;
        return Ok(json!(true));
    }

    let script = format!(
        "try {{ const value=await window.tutorialz[{}]({}); dioxus.send({{ok:true,value}}); }} catch(e) {{ dioxus.send({{ok:false,error:String(e)}}); }}",
        serde_json::to_string(method).unwrap(),
        args,
    );
    let result = document::eval(&script)
        .recv::<Value>()
        .await
        .map_err(|e| e.to_string())?;
    if result["ok"] == true {
        Ok(result["value"].clone())
    } else {
        Err(result["error"]
            .as_str()
            .unwrap_or("Platform operation failed")
            .into())
    }
}
pub async fn uid() -> String {
    call("uid", Value::Null)
        .await
        .ok()
        .and_then(|v| v.as_str().map(String::from))
        .unwrap_or_else(|| format!("id-{}", now()))
}
pub fn now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
pub async fn timestamp() -> u64 {
    call("now", Value::Null)
        .await
        .ok()
        .and_then(|v| v.as_u64())
        .unwrap_or(0)
}
pub async fn load(key: &str) -> Result<Option<String>, String> {
    #[cfg(target_os = "android")]
    {
        return match std::fs::read_to_string(android_file(key)?) {
            Ok(s) => Ok(Some(s)),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(e.to_string()),
        };
    }
    #[cfg(not(target_os = "android"))]
    {
        Ok(call("load", json!(key)).await?.as_str().map(String::from))
    }
}
pub async fn save(key: &str, value: &str) -> Result<(), String> {
    #[cfg(target_os = "android")]
    {
        let path = android_file(key)?;
        let temporary = path.with_extension("tmp");
        std::fs::write(&temporary, value).map_err(|e| e.to_string())?;
        return std::fs::rename(temporary, path).map_err(|e| e.to_string());
    }
    #[cfg(not(target_os = "android"))]
    {
        call("save", json!({ "key" : key, "value" : value })).await?;
        Ok(())
    }
}
#[cfg(target_os = "android")]
fn android_file(key: &str) -> Result<std::path::PathBuf, String> {
    if !key.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-') {
        return Err("Invalid storage key".into());
    }
    let context = ndk_context::android_context();
    let vm = unsafe { jni::JavaVM::from_raw(context.vm().cast()) }.map_err(|e| e.to_string())?;
    let mut env = vm.attach_current_thread().map_err(|e| e.to_string())?;
    let activity = unsafe { jni::objects::JObject::from_raw(context.context().cast()) };
    let file = env
        .call_method(&activity, "getFilesDir", "()Ljava/io/File;", &[])
        .and_then(|v| v.l())
        .map_err(|e| e.to_string())?;
    let path = env
        .call_method(file, "getAbsolutePath", "()Ljava/lang/String;", &[])
        .and_then(|v| v.l())
        .map_err(|e| e.to_string())?;
    let path = jni::objects::JString::from(path);
    let text: String = env.get_string(&path).map_err(|e| e.to_string())?.into();
    Ok(std::path::PathBuf::from(text).join(format!("{key}.json")))
}
pub fn markdown(text: &str) -> String {
    use pulldown_cmark::{html, Event, Options, Parser};
    let events =
        Parser::new_ext(text, Options::ENABLE_TABLES | Options::ENABLE_STRIKETHROUGH).map(|e| {
            match e {
                Event::Html(t) | Event::InlineHtml(t) => Event::Text(t),
                Event::Start(pulldown_cmark::Tag::Link {
                    link_type,
                    dest_url,
                    title,
                    id,
                }) => {
                    let dest = if dest_url.starts_with("https://")
                        || dest_url.starts_with("http://")
                        || dest_url.starts_with('#')
                    {
                        dest_url
                    } else {
                        "#".into()
                    };
                    Event::Start(pulldown_cmark::Tag::Link {
                        link_type,
                        dest_url: dest,
                        title,
                        id,
                    })
                }
                Event::Start(pulldown_cmark::Tag::Image { .. }) => {
                    Event::Text("[image omitted for offline portability]".into())
                }
                Event::End(pulldown_cmark::TagEnd::Image) => Event::Text("".into()),
                other => other,
            }
        });
    let mut html = String::new();
    html::push_html(&mut html, events);
    html
}
#[component]
pub fn Markdown(text: String) -> Element {
    rsx! {
        div { class: "markdown", dangerous_inner_html: markdown(&text) }
    }
}
#[component]
pub fn Difficulty(value: String, onchange: EventHandler<String>, all: bool) -> Element {
    rsx! {
        select { value, onchange: move |e| onchange.call(e.value()),
            if all {
                option { value: "all", "All difficulties" }
            }
            option { value: "easy", "Easy" }
            option { value: "medium", "Medium" }
            option { value: "hard", "Hard" }
        }
    }
}
pub fn kind_name(q: &Question) -> &'static str {
    match q.kind {
        QuestionKind::Choice { multiple: true, .. } => "Multiple select",
        QuestionKind::Choice { .. } => "Multiple choice",
        QuestionKind::Blanks { .. } => "Fill in the blanks",
        QuestionKind::Java {
            style: JavaStyle::Snippet,
            ..
        } => "Missing code",
        QuestionKind::Java { .. } => "Write a program",
    }
}
/// Keep stored topic IDs intact while presenting consistent learner-facing names.
pub fn question_topic_label(topic: &str) -> &str {
    match topic.trim() {
        "Java - Servlets" => "Servlets",
        "Java - JSP" => "JSP",
        "Java - OOPS" => "OOP",
        "Java Design Patterns" => "Design Patterns",
        "Java - EJB" => "EJB",
        "Java - JMS" => "JMS",
        topic => topic,
    }
}

#[cfg(test)]
mod topic_tests {
    use super::question_topic_label;

    #[test]
    fn displays_jakarta_topic_names() {
        for (stored, expected) in [
            ("Java Spring", "Java Spring"),
            ("Hibernate", "Hibernate"),
            ("Java - Servlets", "Servlets"),
            ("Java - JSP", "JSP"),
            ("Core Java - General", "Core Java - General"),
            ("Java - OOPS", "OOP"),
            ("Java Design Patterns", "Design Patterns"),
            ("Java - EJB", "EJB"),
            ("Core Java - Java 9", "Core Java - Java 9"),
            ("Java - JMS", "JMS"),
        ] {
            assert_eq!(question_topic_label(stored), expected);
            assert_eq!(question_topic_label(expected), expected);
        }
    }

    #[test]
    fn preserves_other_topics_and_trims_whitespace() {
        assert_eq!(question_topic_label(" ActiveMQ "), "ActiveMQ");
        assert_eq!(question_topic_label(" Java - JMS "), "JMS");
        assert_eq!(question_topic_label("  "), "");
    }
}

#[component]
pub fn QuestionSource(question: Question) -> Element {
    let topic = question.topic.as_deref().map(question_topic_label);
    rsx! {
        div { class: "question-source small muted",
            if let Some(topic) = topic.filter(|topic| !topic.is_empty()) {
                span { class: "badge question-topic", "Topic: {topic}" }
            }
            if let Some(origin) = &question.origin {
                span { class: "badge",
                    match origin { QuestionOrigin::Ai => "AI", QuestionOrigin::Scraped => "Scraped" }
                }
            }
            if let Some(url) = &question.source_url {
                if url.starts_with("https://") {
                    a { href: url.clone(), target: "_blank", rel: "noopener noreferrer", "Source" }
                }
            }
            if let Some(attribution) = &question.attribution {
                span { "{attribution.author}" }
                if attribution.license_url.starts_with("https://") {
                    a { href: attribution.license_url.clone(), target: "_blank", rel: "noopener noreferrer",
                        "{attribution.license}"
                    }
                }
                span { "{attribution.notes}" }
            }
        }
    }
}

/// Render the saved submission against the session's question snapshot.
/// Student input is rendered as text, never interpreted as Markdown or HTML.
#[component]
pub fn SubmittedAnswer(question: Question, answer: Option<Answer>) -> Element {
    rsx! {
        div { class: "submitted-answer",
            strong { "Your answer" }
            match answer {
                None => rsx! { p { "No answer submitted." } },
                Some(Answer::Skipped) => rsx! { p { "You skipped this question." } },
                Some(Answer::Choice(selected)) => {
                    if let QuestionKind::Choice { options, .. } = &question.kind {
                        rsx! {
                            if selected.is_empty() { p { "No option selected." } }
                            ul {
                                for index in selected {
                                    li {
                                        if let Some(option) = options.get(index) {
                                            Markdown { text: option.clone() }
                                        } else {
                                            "Selected option is unavailable."
                                        }
                                    }
                                }
                            }
                        }
                    } else { rsx! { p { "Saved answer does not match this question." } } }
                },
                Some(Answer::Blanks(values)) => {
                    if let QuestionKind::Blanks { blanks } = &question.kind {
                        rsx! {
                            dl {
                                for (index, blank) in blanks.iter().enumerate() {
                                    dt { "{blank.label}" }
                                    dd { class: "submitted-value",
                                        if let Some(value) = values.get(index).filter(|v| !v.is_empty()) {
                                            "{value}"
                                        } else {
                                            "(empty)"
                                        }
                                    }
                                }
                            }
                        }
                    } else { rsx! { p { "Saved answer does not match this question." } } }
                },
                Some(Answer::Code(source)) => rsx! { pre { class: "code", "{source}" } },
            }
        }
    }
}
#[component]
pub fn AnswerFields(
    question: Question,
    answer: Answer,
    onchange: EventHandler<Answer>,
    disabled: bool,
) -> Element {
    match question.kind {
        QuestionKind::Choice {
            options, multiple, ..
        } => {
            let selected = if let Answer::Choice(s) = answer {
                s
            } else {
                vec![]
            };
            rsx! {
                div { class: "choices",
                    for (i, label) in options.iter().enumerate() {
                        label { key: "{question.id}-{i}", class: if selected.contains(&i) { "choice selected" } else { "choice" },
                            input {
                                r#type: if multiple { "checkbox" } else { "radio" },
                                name: "answer-{question.id}",
                                checked: selected.contains(&i),
                                disabled,
                                onclick: move |_| {
                                    if !multiple {
                                        onchange.call(Answer::Choice(vec![i]));
                                    }
                                },
                                onchange: {
                                    let selected = selected.clone();
                                    move |_| {
                                        if multiple {
                                            let mut values = selected.clone();
                                            if values.contains(&i) { values.retain(|x| *x != i) } else { values.push(i) }
                                            onchange.call(Answer::Choice(values));
                                        }
                                    }
                                },
                            }
                            span { class: "option-letter", "{((b'A'+i as u8) as char)}" }
                            Markdown { text: label.clone() }
                        }
                    }
                }
            }
        }
        QuestionKind::Blanks { blanks } => {
            let values = if let Answer::Blanks(v) = answer {
                v
            } else {
                vec![String::new(); blanks.len()]
            };
            rsx! {
                for (i, b) in blanks.iter().enumerate() {
                    label { class: "field",
                        "{b.label}"
                        input {
                            value: values.get(i).cloned().unwrap_or_default(),
                            disabled,
                            oninput: {
                                let values = values.clone();
                                let len = blanks.len();
                                move |e| {
                                    let mut v = values.clone();
                                    v.resize(len, String::new());
                                    v[i] = e.value();
                                    onchange.call(Answer::Blanks(v));
                                }
                            },
                        }
                    }
                }
            }
        }
        QuestionKind::Java { starter, .. } => {
            let code = if let Answer::Code(c) = answer {
                c
            } else {
                starter
            };
            rsx! {
                label { class: "field",
                    "Java · Main.java"
                    textarea {
                        class: "code",
                        spellcheck: "false",
                        rows: 14,
                        value: code,
                        disabled,
                        oninput: move |
                                        e | onchange.call(Answer::Code(e.value())),
                    }
                }
            }
        }
    }
}
pub fn initial_answer(q: &Question) -> Answer {
    match &q.kind {
        QuestionKind::Choice { .. } => Answer::Choice(vec![]),
        QuestionKind::Blanks { blanks } => Answer::Blanks(vec![String::new(); blanks.len()]),
        QuestionKind::Java { starter, .. } => Answer::Code(starter.clone()),
    }
}
pub fn solution(q: &Question) -> String {
    match &q.kind {
        QuestionKind::Choice {
            options, correct, ..
        } => correct
            .iter()
            .filter_map(|i| options.get(*i))
            .cloned()
            .collect::<Vec<_>>()
            .join(", "),
        QuestionKind::Blanks { blanks } => blanks
            .iter()
            .map(|b| format!("{}: {}", b.label, b.accepted.join(" / ")))
            .collect::<Vec<_>>()
            .join("\n"),
        QuestionKind::Java { reference, .. } => format!("```java\n{reference}\n```"),
    }
}

#[cfg(target_os = "android")]
fn android_export(name: &str, text: &str) -> Result<(), String> {
    use jni::objects::{JObject, JValue};
    fn run(name: &str, text: &str) -> jni::errors::Result<()> {
        let context = ndk_context::android_context();
        let vm = unsafe { jni::JavaVM::from_raw(context.vm().cast()) }?;
        let mut env = vm.attach_current_thread()?;
        let activity = unsafe { JObject::from_raw(context.context().cast()) };
        let values = env.new_object("android/content/ContentValues", "()V", &[])?;
        for (key, value) in [
            ("_display_name", name),
            ("mime_type", "application/json"),
            ("relative_path", "Download/Tutorialz"),
        ] {
            let key = JObject::from(env.new_string(key)?);
            let value = JObject::from(env.new_string(value)?);
            env.call_method(
                &values,
                "put",
                "(Ljava/lang/String;Ljava/lang/String;)V",
                &[JValue::Object(&key), JValue::Object(&value)],
            )?;
        }
        let resolver = env
            .call_method(
                &activity,
                "getContentResolver",
                "()Landroid/content/ContentResolver;",
                &[],
            )?
            .l()?;
        let downloads = env
            .get_static_field(
                "android/provider/MediaStore$Downloads",
                "EXTERNAL_CONTENT_URI",
                "Landroid/net/Uri;",
            )?
            .l()?;
        let uri = env
            .call_method(
                &resolver,
                "insert",
                "(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;",
                &[JValue::Object(&downloads), JValue::Object(&values)],
            )?
            .l()?;
        let stream = env
            .call_method(
                &resolver,
                "openOutputStream",
                "(Landroid/net/Uri;)Ljava/io/OutputStream;",
                &[JValue::Object(&uri)],
            )?
            .l()?;
        let bytes = JObject::from(env.byte_array_from_slice(text.as_bytes())?);
        env.call_method(&stream, "write", "([B)V", &[JValue::Object(&bytes)])?;
        env.call_method(&stream, "close", "()V", &[])?;
        Ok(())
    }
    run(name, text).map_err(|e| format!("Could not save backup to Downloads/Tutorialz: {e}"))
}
