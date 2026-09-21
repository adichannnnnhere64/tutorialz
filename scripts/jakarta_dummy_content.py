"""Original 200-item practice exam for Spring, Hibernate, messaging, and Java 8/9.

Each theme contributes four different assessable outcomes: mechanism, diagnosis,
design choice, and verification. This deliberately avoids narrative rewordings.
"""
from question_bank import assessment, choice

SPRING = "https://docs.spring.io/spring-framework/reference/"
HIBERNATE = "https://docs.hibernate.org/orm/6.6/userguide/html_single/"
JMS = "https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html"
ARTEMIS = "https://activemq.apache.org/components/artemis/documentation/2.26.0/"
JAVA8 = "https://docs.oracle.com/javase/8/docs/api/"
JAVA9 = "https://docs.oracle.com/javase/9/docs/api/"

# (objective stem, focus, supported statement, plausible wrong statement, reference)
THEMES = {
    "Java Spring": [
        ("proxy-self-invocation", "proxy-based transactional advice", "An external call through the Spring proxy is intercepted; a direct self-invocation is not in default proxy mode.", "Annotating any method guarantees that every call to it is intercepted.", SPRING + "data-access/transaction/declarative/annotations.html"),
        ("required-propagation", "REQUIRED transaction propagation", "REQUIRED joins an existing transaction or starts one when none exists.", "REQUIRED always suspends the caller and starts an independent transaction.", SPRING + "data-access/transaction/declarative/tx-propagation.html"),
        ("requires-new-propagation", "REQUIRES_NEW transaction propagation", "REQUIRES_NEW uses an independent physical transaction and suspends an existing one.", "REQUIRES_NEW merely creates a nested logical scope in the same transaction.", SPRING + "data-access/transaction/declarative/tx-propagation.html"),
        ("qualifier-resolution", "candidate resolution with qualifiers", "A qualifier narrows type-matching bean candidates at an injection point.", "A qualifier changes a bean's lifecycle scope.", SPRING + "core/beans/annotation-config/autowired-qualifiers.html"),
        ("primary-resolution", "primary candidate selection", "@Primary is a preference among otherwise eligible single-valued injection candidates.", "@Primary forces injection even when a qualifier excludes the bean.", SPRING + "core/beans/annotation-config/autowired-primary.html"),
        ("configuration-properties", "externalized configuration binding", "ConfigurationProperties binds grouped external settings to a typed object.", "ConfigurationProperties automatically decrypts every application property.", SPRING + "core/beans/environment.html"),
        ("cache-self-invocation", "proxy-based cache annotations", "A cache annotation on a method is skipped by direct self-invocation in default proxy mode.", "@Cacheable writes cache entries before a method has any return value.", SPRING + "integration/cache/annotations.html"),
        ("async-proxy", "@Async invocation", "@Async takes effect when a caller invokes the proxied Spring bean.", "@Async makes ordinary local method calls asynchronous without proxy involvement.", SPRING + "integration/scheduling.html"),
        ("scheduled-overlap", "scheduled task execution", "A fixed-rate task can overlap if its execution time and scheduler configuration permit it.", "@Scheduled guarantees that a task never overlaps across every deployment node.", SPRING + "integration/scheduling.html"),
        ("aop-order", "ordered cross-cutting advice", "Advice ordering must be specified when transaction, security, and custom aspects require a defined nesting.", "Aspect execution order is always source-file order.", SPRING + "core/aop/ataspectj/advice.html"),
    ],
    "Hibernate": [
        ("persistence-context-identity", "first-level cache identity", "Within one persistence context, repeated loads of the same identifier resolve to the managed instance.", "The first-level cache is shared by every SessionFactory in a cluster.", HIBERNATE + "#persistence-context"),
        ("dirty-checking", "dirty checking", "Hibernate detects changes to managed entity state and synchronizes them during flush.", "Dirty checking persists changes to detached objects without reattachment.", HIBERNATE + "#pc-managed-state"),
        ("flush-commit", "flush versus commit", "Flush synchronizes pending changes with the database; commit completes the transaction.", "Flush commits the database transaction and makes rollback impossible.", HIBERNATE + "#flushing"),
        ("detached-merge", "merging detached state", "merge copies detached state into a managed instance and returns that managed instance.", "merge makes the supplied detached object itself managed.", HIBERNATE + "#pc-merge"),
        ("lazy-initialization", "lazy association initialization", "A lazy association needs an open persistence context when it is first initialized.", "LAZY guarantees no SQL can ever be issued for the association.", HIBERNATE + "#fetching"),
        ("join-fetch-query", "join fetch in entity queries", "JOIN FETCH can load a requested association as part of the query's fetch plan.", "JOIN FETCH changes every future query for the entity globally.", HIBERNATE + "#hql-joins"),
        ("batch-fetch", "batch fetching", "Batch fetching can initialize multiple uninitialized proxies or collections with an IN-style query.", "Batch fetching guarantees one SQL statement for every possible graph shape.", HIBERNATE + "#fetching-batch"),
        ("optimistic-version", "optimistic version checks", "A version predicate detects a conflicting update at write time.", "@Version serializes all reads through one JVM lock.", HIBERNATE + "#locking-optimistic"),
        ("second-level-cache", "second-level cache scope", "The second-level cache is associated with the SessionFactory and needs an explicitly configured provider and strategy.", "The second-level cache is the same per-transaction cache as the persistence context.", HIBERNATE + "#caching"),
        ("query-cache", "query cache semantics", "Query caching caches query results and should be enabled only for suitable, high-hit-rate queries.", "Enabling query cache automatically makes every entity cacheable and immutable.", HIBERNATE + "#caching-query"),
    ],
    "Java - JMS": [
        ("queue-competing-consumers", "queue delivery", "Consumers of one queue compete for messages rather than each receiving a copy.", "Every queue consumer receives every message sent to the queue.", JMS + "#point-to-point"),
        ("topic-subscription", "topic subscriptions", "A topic subscription represents a consumer's stream of published messages.", "A topic always has exactly one consumer and one queue.", JMS + "#publish-subscribe"),
        ("durable-subscription", "durable subscriptions", "A durable topic subscription retains eligible messages while its durable subscriber is disconnected.", "A durable subscription makes a queue message visible to every consumer.", JMS + "#durable-subscriptions"),
        ("client-ack", "CLIENT_ACKNOWLEDGE scope", "In CLIENT_ACKNOWLEDGE, acknowledging a message acknowledges messages consumed by that session.", "CLIENT_ACKNOWLEDGE acknowledges only the exact message object and no earlier deliveries.", JMS + "#reliability"),
        ("transacted-session", "local JMS transactions", "A transacted Session commits or rolls back its sends and receives as a messaging unit.", "A transacted Session automatically includes arbitrary JDBC work in the same transaction.", JMS + "#transactions"),
        ("message-selector", "message selectors", "A selector filters on message headers and properties rather than parsing an arbitrary body field.", "A selector evaluates JSON fields in every message body by default.", JMS + "#message-selectors"),
        ("ttl-expiration", "message expiration", "Time-to-live sets expiry semantics; it is not a request to delay first delivery.", "A message with a TTL is guaranteed to be delivered exactly at expiry time.", JMS + "#message-expiration"),
        ("delivery-delay", "delivery delay", "Delivery delay expresses an earliest delivery time before a provider dispatches a sent message.", "Delivery delay changes a message into a durable topic subscription.", JMS + "#delivery-delay"),
        ("redelivery-idempotency", "at-least-once redelivery", "A consumer should make the business operation idempotent when redelivery can follow a failure.", "JMS redelivery guarantees a business operation has never already committed.", JMS + "#reliability"),
        ("request-reply-correlation", "request-reply correlation", "A requester uses a correlation identifier to match a reply with its outstanding request.", "JMSReplyTo itself uniquely identifies every request without a correlation value.", JMS + "#request-reply"),
    ],
    "ActiveMQ Artemis": [
        ("address-queue-model", "Artemis address and queue model", "An address can have zero or more queues, and queues are bound to addresses.", "An Artemis address is always exactly one physical queue.", ARTEMIS + "address-model.html"),
        ("anycast-routing", "anycast routing", "Anycast routes a message to one matching queue in a point-to-point pattern.", "Anycast copies every message to every queue on an address.", ARTEMIS + "address-model.html"),
        ("multicast-routing", "multicast routing", "Multicast routes a message to every matching queue on an address.", "Multicast selects exactly one queue using round-robin delivery.", ARTEMIS + "address-model.html"),
        ("dead-letter-address", "dead-letter handling", "A dead-letter address receives messages after configured unsuccessful delivery attempts.", "A dead-letter address permanently disables acknowledgment for all consumers.", ARTEMIS + "undelivered-messages.html"),
        ("redelivery-delay", "broker redelivery delay", "A redelivery delay spaces retries after a cancelled or rolled-back delivery.", "A redelivery delay changes the original producer's message priority.", ARTEMIS + "undelivered-messages.html"),
        ("expiry-address", "broker expiry routing", "An expiry address can receive messages that expire according to their expiry settings.", "An expiry address is where all successfully acknowledged messages are stored.", ARTEMIS + "message-expiry.html"),
        ("consumer-window", "consumer flow control", "Consumer window size limits buffered message credit and affects client-side flow control.", "Consumer window size is the retention period for durable messages.", ARTEMIS + "client-reconnection.html"),
        ("large-message", "large-message storage", "Large-message handling streams oversized message bodies rather than requiring one normal in-memory payload.", "Large-message handling converts every message into a persistent queue automatically.", ARTEMIS + "large-messages.html"),
        ("security-role", "address security roles", "Security roles grant operations such as send, consume, create, or manage for matched addresses.", "A role grants administrative access to every address regardless of match rules.", ARTEMIS + "security.html"),
        ("ha-reconnect", "client reconnection", "Reconnect and failover behavior requires explicit client and broker configuration appropriate to delivery guarantees.", "A reconnect always proves that an in-flight send was processed exactly once.", ARTEMIS + "client-reconnection.html"),
    ],
    "Core Java - Java 8": [
        ("stream-laziness", "stream laziness", "Intermediate stream operations are lazy and run when a terminal operation consumes the stream.", "Creating a stream pipeline immediately executes every intermediate operation.", JAVA8 + "java/util/stream/package-summary.html"),
        ("stream-single-use", "stream lifecycle", "A stream must not be reused after a terminal operation has consumed it.", "A terminal operation resets a stream so it can be traversed again.", JAVA8 + "java/util/stream/Stream.html"),
        ("optional-or-else", "Optional eager fallback", "orElse evaluates its argument before the call, while orElseGet invokes its supplier only when needed.", "orElseGet always computes its supplier before checking Optional presence.", JAVA8 + "java/util/Optional.html"),
        ("completablefuture-exception", "CompletableFuture failure propagation", "A dependent stage can observe and transform exceptional completion using exception-handling methods.", "CompletableFuture silently converts every exception into a successful null value.", JAVA8 + "java/util/concurrent/CompletableFuture.html"),
        ("java-time-immutability", "java.time value types", "Core java.time classes such as LocalDate are immutable value types.", "LocalDate mutates its receiver when plusDays is called.", JAVA8 + "java/time/LocalDate.html"),
    ],
    "Core Java - Java 9": [
        ("module-requires", "module readability", "requires declares that one named module depends on another module.", "requires exports all packages of the required module to every client.", JAVA9 + "java/lang/module/package-summary.html"),
        ("module-exports", "package exports", "exports makes a package's public types accessible to reading modules.", "exports grants deep reflection on every private member in the package.", JAVA9 + "java/lang/module/package-summary.html"),
        ("module-opens", "reflective opens", "opens grants runtime deep reflection for a package without making it ordinary API export.", "opens lets any module compile against all non-public package types.", JAVA9 + "java/lang/module/package-summary.html"),
        ("list-factory", "immutable collection factories", "List.of creates a structurally unmodifiable list and rejects null elements.", "List.of creates a mutable ArrayList that permits null values.", JAVA9 + "java/util/List.html"),
        ("optional-stream", "Optional.stream", "Optional.stream produces a one-element stream when present and an empty stream otherwise.", "Optional.stream throws when the Optional is empty.", JAVA9 + "java/util/Optional.html"),
    ],
}


def course():
    questions = []
    for topic, themes in THEMES.items():
        for stem, focus, truth, misconception, source in themes:
            variants = [
                ("mechanism", "recall", f"Which statement correctly describes {focus}?", truth,
                 [misconception, f"{focus.capitalize()} is only a compile-time naming convention.", f"{focus.capitalize()} applies only to unrelated browser requests."],
                 f"{truth} The misconception confuses this mechanism with a different boundary."),
                ("diagnosis", "debug", f"A team assumes that {misconception[0].lower() + misconception[1:]} What should the review identify?", truth,
                 ["The assumption is valid whenever the application uses annotations.", "The behavior is determined only by Java source-file order.", "The behavior changes only when the process is restarted."],
                 f"The review should correct the assumption: {truth}"),
                ("design", "design", f"A design depends on {focus}. Which requirement should be made explicit before implementation?", truth,
                 [misconception, "No requirement is needed because the runtime infers all business guarantees.", "The feature can be treated as a replacement for authorization and data validation."],
                 f"A sound design states the actual mechanism and its boundary: {truth}"),
                ("verification", "apply", f"Which verification most directly tests the intended behavior of {focus}?", f"Create a focused integration scenario that demonstrates: {truth}",
                 [f"Assert only that the application starts, without exercising {focus}.", "Inspect annotation names without observing runtime behavior.", "Rely on a single successful manual request with no controlled failure case."],
                 f"Runtime behavior needs an observable scenario. The expected result is: {truth}"),
            ]
            for variant, kind, prompt, answer, wrong, explanation in variants:
                objective = f"jakarta-dummy-{stem}-{variant}"
                questions.append(choice(
                    objective, prompt, answer, wrong, explanation, topic, source,
                    assessment(objective, kind, f"dummy-{stem}-{variant}"),
                    "hard" if variant in {"design", "verification"} else "medium",
                ))
    assert len(questions) == 200
    return {
        "schema_version": 1,
        "id": "jakarta-dummy-exam",
        "title": "Jakarta Dummy Exam",
        "description": "200 original single-answer scenarios covering Spring, Hibernate, Jakarta Messaging, ActiveMQ Artemis, and Java 8/9 features. Java 8 and Java 9 questions state their applicable release; ActiveMQ questions target Artemis concepts.",
        "subject": "Java Enterprise / Jakarta EE",
        "difficulty": "hard",
        "lessons": [],
        "tests": [{
            "id": "jakarta-dummy-exam-test",
            "title": "Jakarta Dummy Exam",
            "description": "Complete 200-item practice exam. Select all 200 questions and keep difficulty set to All difficulties.",
            "difficulty": "hard",
            "questions": questions,
        }],
    }
