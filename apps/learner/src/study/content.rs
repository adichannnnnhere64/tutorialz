pub struct Topic {
    pub id: &'static str,
    pub title: &'static str,
    pub group: &'static str,
    pub summary: &'static str,
    pub keywords: &'static str,
    pub body: &'static str,
}
impl Topic {
    pub fn sections(&self) -> Vec<(&'static str, &'static str)> {
        self.body
            .trim_start_matches("## ")
            .split("\n## ")
            .filter_map(|part| {
                let (title, body) = part.split_once('\n')?;
                (!title.trim().is_empty()).then_some((title.trim(), body.trim()))
            })
            .collect()
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
