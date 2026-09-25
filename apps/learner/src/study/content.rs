use tutorialz_core::StudyProgress;

pub struct StudySection {
    pub id: String,
    pub title: &'static str,
    pub body: &'static str,
}

pub fn slug(title: &str) -> String {
    title
        .to_lowercase()
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

// Headings inside fenced examples are content, not navigation boundaries.
fn heading_starts(text: &'static str, prefix: &str) -> Vec<(usize, usize, &'static str)> {
    let mut starts = Vec::new();
    let mut offset = 0;
    let mut fence = None;
    for line in text.split_inclusive('\n') {
        let trimmed = line.trim_start();
        if trimmed.starts_with("```") || trimmed.starts_with("~~~") {
            let marker = &trimmed[..3];
            if fence == Some(marker) {
                fence = None;
            } else if fence.is_none() {
                fence = Some(marker);
            }
        } else if fence.is_none() {
            if let Some(title) = line.strip_prefix(prefix) {
                starts.push((offset, offset + line.len(), title.trim()));
            }
        }
        offset += line.len();
    }
    starts
}

fn headings(text: &'static str, prefix: &str) -> Vec<(&'static str, &'static str)> {
    let starts = heading_starts(text, prefix);
    starts
        .iter()
        .enumerate()
        .map(|(i, (_, body_start, title))| {
            let end = starts.get(i + 1).map(|s| s.0).unwrap_or(text.len());
            (*title, text[*body_start..end].trim())
        })
        .collect()
}

impl StudySection {
    pub fn subtopics(&self) -> Vec<(&'static str, &'static str)> {
        headings(self.body, "### ")
    }
    pub fn introduction(&self) -> &'static str {
        heading_starts(self.body, "### ")
            .first()
            .map(|(offset, _, _)| self.body[..*offset].trim())
            .unwrap_or(self.body)
    }
}

pub struct Topic {
    pub id: &'static str,
    pub title: &'static str,
    pub group: &'static str,
    pub summary: &'static str,
    pub keywords: &'static str,
    pub body: &'static str,
}
impl Topic {
    pub fn sections(&self) -> Vec<StudySection> {
        headings(self.body, "## ")
            .into_iter()
            .map(|(title, body)| StudySection {
                id: slug(title),
                title,
                body,
            })
            .collect()
    }
    pub fn resume(&self, progress: &StudyProgress) -> usize {
        self.sections()
            .iter()
            .position(|s| s.id == progress.section_id())
            .unwrap_or(0)
    }
    pub fn search_sections(&self, query: &str) -> Vec<(usize, Option<usize>, String)> {
        if query.trim().is_empty() {
            return vec![];
        }
        let matches = |text: &str| {
            let text = format!("{} {text}", self.title).to_lowercase();
            query
                .split_whitespace()
                .all(|word| text.contains(&word.to_lowercase()))
        };
        let mut results = Vec::new();
        for (position, section) in self.sections().iter().enumerate() {
            let mut found = false;
            for (sub, (title, body)) in section.subtopics().iter().enumerate() {
                if matches(&format!("{title} {body}")) {
                    results.push((position, Some(sub), format!("{} · {title}", section.title)));
                    found = true;
                }
            }
            if !found && matches(&format!("{} {}", section.title, section.body)) {
                results.push((position, None, section.title.to_owned()));
            }
        }
        results
    }
    pub fn matches(&self, query: &str) -> bool {
        let text = format!(
            "{} {} {} {} {}",
            self.title, self.group, self.summary, self.keywords, self.body
        )
        .to_lowercase();
        query
            .split_whitespace()
            .all(|word| text.contains(&word.to_lowercase()))
    }
}
macro_rules! topic {
    ($id:literal, $title:literal, $group:literal, $summary:literal, $keywords:literal) => {
        Topic {
            id: $id,
            title: $title,
            group: $group,
            summary: $summary,
            keywords: $keywords,
            body: include_str!(concat!("../../study/", $id, ".md")),
        }
    };
}
pub const TOPICS: &[Topic] = &[
    topic!("core-java", "Core Java", "Java foundations", "Types, operators, control flow, strings, arrays and methods.", "Core Java - General primitives syntax conversion Scanner Math"),
    topic!("oop", "Java OOP", "Java foundations", "Objects, inheritance, interfaces, equality and generics.", "Java - OOPS polymorphism encapsulation overriding overloading"),
    topic!("collections", "Collections & generics", "Java foundations", "Lists, maps, sets, ordering and safe generic APIs.", "HashMap TreeSet comparator wildcard PECS"),
    topic!("exceptions-io", "Exceptions, I/O & dates", "Java foundations", "Resource ownership, exception flow, files, money and time.", "try catch finally suppressed BigDecimal java.time NIO"),
    topic!("concurrency", "Concurrency", "Java foundations", "Thread safety, executors, cancellation and bounded work.", "synchronized volatile deadlock CompletableFuture atomic"),
    topic!("java8", "Java 8", "Java versions", "Lambdas, functional interfaces, streams and Optional.", "Core Java - Java 8 default methods method references collectors"),
    topic!("java9", "Java 9", "Java versions", "Modules, private interface methods, Flow and stream additions.", "Core Java - Java 9 JPMS jdeps jshell multi-release jar takeWhile"),
    topic!("modern-java", "Java 17 & 21", "Java versions", "Records, sealed classes, pattern matching and virtual threads.", "modernization latest technology industry trends sequenced collections"),
    topic!("patterns", "Design patterns", "Application design", "Choose a pattern for a specific responsibility or constraint.", "Java Design Patterns strategy factory builder adapter decorator visitor command flyweight"),
    topic!("spring", "Spring", "Frameworks & persistence", "Dependency injection, scopes, proxies, transactions and caching.", "Java Spring AOP configuration bean qualifier AOT reactive"),
    topic!("spring-web", "Spring Boot & MVC", "Frameworks & persistence", "Configuration, HTTP endpoints, validation and application tests.", "Spring REST controller profiles application.properties actuator"),
    topic!("hibernate", "Hibernate", "Frameworks & persistence", "Entity lifecycle, mappings, fetch plans, locking and diagnostics.", "Hibernate JPA Jakarta Persistence Session EntityManager N+1"),
    topic!("transactions", "SQL, JDBC & transactions", "Frameworks & persistence", "Atomic changes, isolation, pools and transaction boundaries.", "JTA XA outbox rollback savepoint optimistic pessimistic SQL"),
    topic!("servlets", "Servlets", "Jakarta web & services", "Requests, filters, sessions, lifecycle and asynchronous I/O.", "Java - Servlets encoding multipart RequestDispatcher ServletContext"),
    topic!("jsp", "JSP & Jakarta Pages", "Jakarta web & services", "Views, EL, tag libraries, encoding and error pages.", "Java - JSP JSTL Jakarta Tags c:url c:out JspFragment"),
    topic!("cdi", "CDI", "Jakarta web & services", "Injection, contextual scopes, events, producers and interceptors.", "Contexts Dependency Injection qualifiers alternatives decorators passivation"),
    topic!("ejb", "EJB", "Jakarta web & services", "Session beans, container transactions, timers and role boundaries.", "Java - EJB Enterprise Beans stateful stateless singleton MDB JNDI"),
    topic!("rest", "REST & HTTP", "Jakarta web & services", "Resources, status codes, Jakarta REST clients and API contracts.", "JAX-RS JSON-B JSON-P content negotiation ETag idempotency"),
    topic!("jms", "JMS", "Messaging", "Queues, topics, acknowledgments, transactions and message lifecycles.", "Java - JMS Jakarta Messaging selectors durable subscription delivery delay TTL"),
    topic!("activemq", "ActiveMQ", "Messaging", "Artemis addresses, queues, redelivery, dead letters and operations.", "ActiveMQ Artemis Classic ANYCAST MULTICAST broker prefetch paging HA"),
    topic!("security", "Security & validation", "Delivery & architecture", "Authentication, authorization, input validation and safe output.", "Jakarta Security Bean Validation CSRF XSS secrets TLS roles"),
    topic!("servers", "Jakarta EE & application servers", "Delivery & architecture", "Profiles, deployment artifacts, managed services and compatibility.", "Java EE WildFly Payara Open Liberty TomEE Tomcat Jetty WAR EAR"),
    topic!("testing-deployment", "Testing, tools & deployment", "Delivery & architecture", "Build repeatably, test real boundaries and diagnose production failures.", "Maven Gradle JUnit Mockito tools assets functional domain solutioning implementation"),
    topic!("architecture", "Architecture & business processes", "Delivery & architecture", "Service boundaries, distributed workflows and resilient integration.", "Design Architecture Framework Business-Process domain saga circuit breaker AI observability"),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn headings_in_fenced_examples_are_not_sections() {
        let text = "## Understand\nIntro\n```text\n## fake\n### fake subtopic\n```\n### Real\nBody\n## Apply\nExample\n";
        let parts = headings(text, "## ");
        assert_eq!(parts.len(), 2);
        assert_eq!(parts[0].0, "Understand");
        let subsections = headings(parts[0].1, "### ");
        assert_eq!(subsections, vec![("Real", "Body")]);
        let section = StudySection {
            id: "test".into(),
            title: "Test",
            body: "```text\n### Same title\n```\n### Same title\nActual content",
        };
        assert_eq!(section.introduction(), "```text\n### Same title\n```");
        assert_eq!(section.subtopics(), vec![("Same title", "Actual content")]);
    }

    #[test]
    fn every_chapter_has_the_same_stable_section_contract() {
        for topic in TOPICS {
            let parts = topic.sections();
            assert_eq!(
                parts.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(),
                [
                    "understand",
                    "apply",
                    "advanced",
                    "production",
                    "exam-reasoning",
                    "cheatsheet",
                    "check-yourself",
                    "sources"
                ]
            );
            for (index, part) in parts.iter().enumerate() {
                let mut progress = StudyProgress::default();
                progress.visit(topic.id, &part.id);
                assert_eq!(topic.resume(&progress), index);
            }
        }
    }

    #[test]
    fn section_ids_preserve_original_backup_meaning() {
        let topic = TOPICS.iter().find(|topic| topic.id == "patterns").unwrap();
        for (legacy, name) in [
            "Understand",
            "Apply",
            "Cheatsheet",
            "Check yourself",
            "Sources",
        ]
        .iter()
        .enumerate()
        {
            let progress = StudyProgress {
                last_section: legacy,
                ..Default::default()
            };
            assert_eq!(topic.sections()[topic.resume(&progress)].title, *name);
        }
        let progress = StudyProgress {
            last_section_id: Some("removed-section".into()),
            ..Default::default()
        };
        assert_eq!(topic.resume(&progress), 0);
    }

    #[test]
    fn factory_and_builder_search_returns_named_subtopics() {
        let topic = TOPICS.iter().find(|topic| topic.id == "patterns").unwrap();
        assert!(topic
            .search_sections("Factory Method")
            .iter()
            .any(|(_, sub, label)| sub.is_some() && label.contains("Example P2")));
        assert!(topic
            .search_sections("Builder")
            .iter()
            .any(|(_, sub, label)| sub.is_some() && label.contains("Example P4")));
        assert!(topic.search_sections("   ").is_empty());
    }
}
