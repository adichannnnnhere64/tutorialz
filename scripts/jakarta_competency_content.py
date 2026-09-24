"""Original, scenario-based enterprise Java competency practice.

This is an independent practice blueprint, not an Accenture exam reconstruction.
Every row defines a distinct decision; categories do not generate question variants.
"""
from question_bank import assessment, choice

AREAS = (
    "Basic, Development, Programming and Configuration Knowledge",
    "Design, Architecture, Framework and Business-Process Knowledge",
    "Solutioning, Deployment and Implementation Knowledge",
    "Tools, Assets, Functional and Domain Knowledge",
    "Latest Technology and Industry Trends",
)
TOPICS = (
    "Java Spring", "Hibernate", "Java - Servlets", "Java - JSP",
    "Core Java - General", "Java - OOPS", "Java Design Patterns",
    "Java - EJB", "Core Java - Java 9", "Java - JMS",
)
SPRING = "https://docs.spring.io/spring-framework/reference/"
HIBERNATE = "https://docs.hibernate.org/orm/6.6/userguide/html_single/"
SERVLET = "https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html"
PAGES = "https://jakarta.ee/specifications/pages/3.1/"
EJB = "https://jakarta.ee/specifications/enterprise-beans/4.0/jakarta-enterprise-beans-spec-core-4.0.html"
JMS = "https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html"
JLS = "https://docs.oracle.com/javase/specs/jls/se17/html/"
JAVA9 = "https://docs.oracle.com/javase/9/docs/api/"


def course():
    questions = []

    def add(topic, area, objective, kind, prompt, answer, wrong, explanation,
            source, concepts, difficulty="medium"):
        q = choice(f"jakarta-competency-{objective}", prompt, answer, wrong,
                   explanation, TOPICS[topic], source,
                   assessment(f"jakarta-competency-{objective}", kind, *concepts), difficulty)
        q["second_topic"] = AREAS[area]
        questions.append(q)

    add(0, 0, "qualifier-over-primary", "apply",
        "A Spring application registers two PaymentGateway beans. CardGateway is @Primary; BankGateway has @Qualifier(\"bank\"). A constructor parameter is annotated @Qualifier(\"bank\"). With no other candidates, which gateway is injected?",
        "BankGateway, because the qualifier narrows the eligible candidates.",
        ["CardGateway, because @Primary overrides every qualifier.",
         "Both gateways, because any interface parameter receives all implementations.",
         "Neither gateway, because @Primary and @Qualifier cannot coexist."],
        "The bank qualifier leaves BankGateway as the eligible candidate. @Primary only resolves a preference among eligible beans. A single PaymentGateway parameter receives one bean, and using @Primary on a different bean is not a configuration conflict.",
        SPRING + "core/beans/annotation-config/autowired-qualifiers.html", ["spring-qualifiers", "spring-primary"])
    add(0, 1, "required-rollback-only", "debug",
        "Using Spring's default transaction settings, an outer REQUIRED method calls a separate bean's REQUIRED method through its proxy. The inner method throws an unchecked exception after a database write. The outer method catches it and returns normally. What happens when the outer boundary tries to commit?",
        "Commit fails with UnexpectedRollbackException because the shared transaction is rollback-only.",
        ["The inner changes roll back independently and the outer changes commit.",
         "All changes commit because the outer method caught the exception.",
         "The inner write is rolled back to a savepoint, and the outer transaction commits."],
        "Both REQUIRED methods share the same physical transaction. The inner proxy marks it rollback-only when the unchecked exception escapes. Catching that exception does not undo the mark. There is no independent inner commit, savepoint recovery, or automatic retry, so the outer commit raises UnexpectedRollbackException.",
        SPRING + "data-access/transaction/declarative/tx-propagation.html", ["spring-required", "rollback-only"], "hard")
    add(0, 2, "requires-new-pool-starvation", "debug",
        "Ten concurrent Spring requests each hold a JDBC connection in an outer transaction. Each then calls REQUIRES_NEW through another bean. The pool has ten connections and all requests wait for a second connection. What deployment change addresses this specific stall?",
        "Budget pool capacity and admission limits for simultaneous outer and independent inner transactions.",
        ["Increase the HTTP thread limit while keeping the same JDBC pool.",
         "Disable transaction timeouts so every request can wait indefinitely.",
         "Mark the inner method readOnly so REQUIRES_NEW reuses the outer transaction."],
        "Each suspended outer transaction keeps its connection while the inner transaction needs another. Admission limits and sufficient pool capacity address that demand. More request threads increase contention; a longer timeout only postpones failure. readOnly does not make REQUIRES_NEW reuse the outer transaction.",
        SPRING + "data-access/transaction/declarative/tx-propagation.html", ["spring-requires-new", "connection-pool-boundaries"], "hard")
    add(0, 3, "test-real-commit", "design",
        "A Spring integration test is itself @Transactional and rolls back after calling an order service. It asserts the returned object but never commits. Production reports a deferred database constraint violation at commit. Which test addition targets the missing behavior?",
        "Exercise a real commit boundary and verify the outcome using a separate transaction.",
        ["Mock the repository and assert that save was called once.",
         "Keep rollback-only tests and assert that the entity has a generated ID.",
         "Read the saved row again before the test transaction rolls back."],
        "A transaction that always rolls back never exercises commit-time constraint checking. Commit explicitly and check the result from a separate transaction. A mocked save call, an assigned ID, or an ordinary read inside the original transaction cannot establish that the database would accept the commit.",
        SPRING + "testing/testcontext-framework/tx.html", ["spring-test-transactions", "deferred-constraints"])
    add(0, 4, "aot-runtime-bean-discovery", "design",
        "A Spring application discovers arbitrary plugin classes from names in a database and registers new bean definitions at runtime. The team plans a Spring AOT native image. Which design assumption needs to change?",
        "The bean graph and required reflective access must be known during AOT processing; arbitrary late plugins need another deployment model.",
        ["All classes reachable on a JVM are automatically discoverable in any native image.",
         "Runtime hints allow previously unknown plugin classes to be downloaded after image creation.",
         "Scanning an external plugin directory at startup discovers classes omitted from the native image."],
        "Spring AOT processes the bean definitions at build time, and a native image needs its dynamic access requirements described in advance. Runtime hints can cover known reflective operations; they do not allow arbitrary new classes to be loaded later. Changing discovery location or bean-selection annotations does not remove that constraint.",
        SPRING + "core/aot.html", ["spring-aot", "native-image-reachability"], "hard")

    add(1, 0, "owning-side-association", "debug",
        "Hibernate maps Order.lines with @OneToMany(mappedBy=\"order\") and Line.order with @ManyToOne. Both objects are managed. Code adds a line to order.getLines() but leaves line.order null. Which change makes the foreign-key relationship explicit?",
        "Set line.order to the order and keep both sides of the in-memory relationship consistent.",
        ["Add CascadeType.ALL only; cascade automatically assigns the owning field.",
         "Call flush twice; the second flush infers the missing owning side.",
         "Mark the inverse collection EAGER so reads write the foreign key."],
        "Line.order owns the foreign-key relationship; mappedBy identifies Order.lines as the inverse side. Set the owning field and maintain the collection consistently. Cascading propagates persistence operations, flushing sends pending state, and eager fetching controls reads. None of these assigns a missing owning-side reference.",
        HIBERNATE + "#associations-one-to-many-bidirectional", ["association-owning-side"])
    add(1, 1, "bulk-update-managed-state", "debug",
        "A Hibernate session loads Account 7 with status OPEN. In the same transaction, a bulk HQL update sets matching accounts to CLOSED. No refresh or clear occurs. What should code assume about the already-managed Account object?",
        "Its status can remain OPEN because bulk updates bypass synchronization of managed object state.",
        ["Its status is guaranteed to change to CLOSED before the query returns.",
         "It becomes detached automatically as soon as any bulk statement executes.",
         "Reading its getter always executes a select and refreshes every field."],
        "Bulk HQL updates database rows without rewriting fields in existing managed instances. An affected object can therefore remain stale until explicitly refreshed or reloaded in a new context. The update neither detaches every object nor makes normal getters requery the database.",
        HIBERNATE + "#batch-bulk-hql", ["bulk-dml", "persistence-context"])
    add(1, 2, "identity-insert-batching", "debug",
        "A Hibernate ORM 6.6 import sets hibernate.jdbc.batch_size=50, but inserts for an entity using an IDENTITY identifier are not JDBC-batched. The supported database also offers sequences. Which diagnosis should guide a measured optimization?",
        "IDENTITY generation prevents Hibernate insert batching here; evaluate a supported sequence-based strategy and its schema migration.",
        ["The batch size must be set to the total row count before any identifier strategy can batch.",
         "IDENTITY batches only when every entity is retained in the persistence context until the final commit.",
         "Adding a second-level cache region automatically converts identity inserts into JDBC batches."],
        "Hibernate ORM 6.6 disables JDBC insert batching for IDENTITY-generated identifiers. Sequence-based generation can allow batching, subject to database support and a safe identifier migration. A larger batch size, a longer-lived persistence context, and second-level caching do not remove the identity-generation restriction.",
        HIBERNATE + "#batch-session-batch-insert", ["hibernate-identity-batching"], "hard")
    add(1, 3, "measure-query-growth", "apply",
        "An order-list endpoint is suspected of N+1 queries. A warm second-level cache hides the issue in a local test. Which measurement best reveals how its database work scales with page size?",
        "Measure SQL statement counts for several page sizes with controlled cold-cache fixtures.",
        ["Count repository method invocations without observing generated SQL.",
         "Measure only the fastest warm-cache request for a one-order fixture.",
         "Check whether the entity annotations contain FetchType.LAZY."],
        "SQL counts over controlled, cold-cache fixtures reveal whether database work grows with the number of returned orders. Repository-call counts hide ORM-generated statements. A warm one-row measurement can hide repeated selects, and a LAZY annotation alone does not describe the executed fetch plan.",
        HIBERNATE + "#statistics", ["hibernate-statistics", "n-plus-one-queries"])
    add(1, 4, "record-embeddable-not-entity", "apply",
        "A Java 17 service uses Hibernate ORM 6.6 and Jakarta Persistence 3.1. The team wants to model an immutable Money value with a record. Which option respects this provider/version combination?",
        "Use Hibernate's record embeddable support for Money, while keeping entity classes compliant with entity requirements.",
        ["Mark every record @Entity because records satisfy the non-final entity requirement.",
         "Give the record a mutable public no-argument constructor to make it an entity.",
         "Assume record embeddables are portable to every Persistence 3.1 provider."],
        "Hibernate ORM 6.6 supports record embeddables, but a record is final and does not satisfy ordinary entity-class requirements for the stated Persistence 3.1 baseline. Adding an annotation or constructor does not remove those restrictions. Hibernate support also does not prove portability to every Persistence 3.1 provider.",
        HIBERNATE + "#embeddable", ["record-embeddables", "provider-portability"])

    add(2, 0, "servlet-mapping-precedence", "apply",
        "A Servlet web app has mappings /reports/*, *.csv, and /. For a request to /app/reports/daily.csv in context /app, which mapping wins?",
        "/reports/*, because a matching path mapping precedes an extension mapping.",
        ["*.csv, because extension mappings always precede path mappings.",
         "/, because it matches the first slash in every request.",
         "The mapping declared last, because declaration order breaks this tie."],
        "After removing /app, the container evaluates /reports/daily.csv. Exact matches take priority, followed by the longest matching path mapping, an extension mapping, and the default mapping. /reports/* therefore wins; neither declaration order nor the .csv suffix overrides it.",
        SERVLET + "#mapping-requests-to-servlets", ["servlet-mapping-precedence"])
    add(2, 1, "async-dispatch-filter", "debug",
        "A Servlet filter is asyncSupported=true but mapped only to DispatcherType.REQUEST. An endpoint starts async processing and later calls AsyncContext.dispatch(). The filter must also run on that redispatch. What configuration is missing?",
        "Include DispatcherType.ASYNC in the filter mapping and make its behavior safe for redispatch.",
        ["Set asyncSupported=false so the filter intercepts asynchronous completion.",
         "Map only DispatcherType.FORWARD because every async dispatch is a forward.",
         "Call startAsync twice so the original REQUEST filter executes again."],
        "asyncSupported allows asynchronous processing, while dispatcher types determine when a filter runs. AsyncContext.dispatch uses ASYNC, not REQUEST or FORWARD. Disabling async support prevents the intended processing; starting another async cycle does not repair the mapping.",
        SERVLET + "#asynchronous-processing", ["async-filter-dispatch"])
    add(2, 2, "rotate-session-after-login", "apply",
        "A servlet implements a custom login flow and retains a pre-login shopping cart in HttpSession. After validating credentials, it must mitigate session fixation while retaining those attributes. Which Servlet API operation fits?",
        "Call request.changeSessionId() on the existing session after authentication.",
        ["Keep the same session ID and add a loggedIn=true attribute.",
         "Copy the session ID into the response URL and reuse it for later logins.",
         "Call getSession(false) repeatedly until the container rotates the ID."],
        "changeSessionId rotates the identifier while retaining the existing session and cart attributes. Updating a login attribute does not invalidate the old identifier. Reusing an identifier in a URL preserves the fixation risk, and getSession(false) only retrieves an existing session.",
        "https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/http/httpservletrequest", ["session-fixation", "session-id-rotation"])
    add(2, 3, "test-request-encoding", "debug",
        "A UTF-8 form POST produces corrupted characters. One filter reads getParameter(\"name\") before a later filter sets the request encoding to UTF-8. Which change fixes the order of decoding?",
        "Set request encoding before any component reads parameters, then test a real UTF-8 form body.",
        ["Set only the response encoding after getParameter and re-read the cached parameter.",
         "Convert the decoded String to UTF-8 bytes without checking the original request encoding.",
         "Put the encoding filter after the controller so it can inspect the rendered output."],
        "The first parameter read may decode and cache the form data. Set the request encoding before that read. Response encoding affects output, not input. Re-encoding an already corrupted String can lose information, and a filter placed after parameter parsing is too late.",
        SERVLET + "#request-data-encoding", ["servlet-request-encoding"])
    add(2, 4, "virtual-thread-servlet-state", "design",
        "A servlet container is configured to run requests on Java 21 virtual threads. A servlet stores currentCustomer in an instance field during each request. What changes about the correctness of this field?",
        "It is still shared across concurrent requests; request-specific customer state must remain isolated.",
        ["It becomes thread-local because a virtual thread owns the servlet instance.",
         "It is safe because virtual threads serialize all calls to service().",
         "It is isolated automatically when the field is declared volatile."],
        "Concurrent requests still use the shared servlet instance, regardless of whether their threads are virtual or platform threads. A request-local variable keeps customer state separate. Neither volatile nor a different thread implementation creates one field per request or serializes service invocations.",
        SERVLET + "#multithreading-issues", ["servlet-instance-concurrency", "virtual-threads"])

    add(3, 0, "jsp-include-translation", "debug",
        "Two JSP fragments both declare a local variable named total in scriptlets. A page combines them using two <%@ include file=... %> directives and fails translation with a duplicate-variable error. Why?",
        "Directive includes merge source into one translation unit, so the declarations can collide.",
        ["Each directive creates a separate servlet and Java forbids equal variable names across servlets.",
         "Directive includes execute only after the response is committed.",
         "JSP directives automatically promote every local variable to session scope."],
        "The include directive inserts fragment source before JSP translation, so scriptlet declarations can end up in the same generated Java scope. Separate source files do not create separate execution scopes in this case. A jsp:include is a runtime inclusion, and session scope is unrelated to Java local-variable declarations.",
        PAGES, ["jsp-directive-include"])
    add(3, 1, "jsp-explicit-scope", "apply",
        "A JSP has page-scope customer='preview' and request-scope customer='approved'. Its summary must display the controller's request value even when a tag creates a page attribute with the same name. Which expression is appropriate?",
        "${requestScope.customer}",
        ["${customer}", "${sessionScope.customer}", "${applicationScope.customer}"],
        "requestScope selects the controller's request attribute directly. The unqualified customer expression finds the page attribute first. sessionScope and applicationScope select different lifetimes and do not fall back to the request value.",
        PAGES, ["jsp-el-scope-resolution"])
    add(3, 2, "jsp-precompile-smoke-test", "design",
        "A WAR compiles in CI, but its first production request to invoice.jsp fails because a tag library is missing. Java compilation did not translate JSP files. Which release check would expose this before users encounter it?",
        "Translate JSPs with the target-compatible tooling and smoke-test rendered pages in the assembled deployment.",
        ["Run javac only on controller sources and assume JSPs share that compilation step.",
         "Check that invoice.jsp exists in source control without inspecting the packaged WAR.",
         "Increase the HTTP request timeout so the missing tag library can be discovered later."],
        "JSP translation resolves tag libraries and generates servlet code. Target-compatible precompilation plus a deployed-page smoke test checks both translation and packaging. Controller compilation, source-file presence, and longer HTTP timeouts cannot supply a missing tag library.",
        PAGES, ["jsp-precompilation", "war-verification"])
    add(3, 3, "jsp-text-output-escaping", "apply",
        "A JSP displays an untrusted comment between ordinary HTML <p> tags. Jakarta Tags is available. Which rendering approach escapes HTML metacharacters for this text context?",
        "Use <c:out value=\"${comment}\"/> with its default escapeXml=true.",
        ["Use ${comment} alone because JSP EL always performs HTML escaping.",
         "Use <c:out value=\"${comment}\" escapeXml=\"false\"/> to enable escaping.",
         "Place the comment in a scriptlet and call out.print(comment) directly."],
        "c:out escapes metacharacters by default, which fits ordinary HTML text content. Plain EL and out.print emit the value without this escaping; escapeXml=false disables it. Other contexts, such as JavaScript or a URL, need context-appropriate handling.",
        "https://jakarta.ee/specifications/tags/3.0/jakarta-tags-spec-3.0", ["jsp-output-encoding"])
    add(3, 4, "pages-four-threadsafe-migration", "debug",
        "A legacy JSP contains <%@ page isThreadSafe=\"false\" %>. It is being migrated to Jakarta Pages 4.0. Which action is required?",
        "Remove the unsupported attribute and make any shared page state safe for concurrent access.",
        ["Keep the attribute because Pages 4.0 guarantees a SingleThreadModel servlet for it.",
         "Retain the attribute and increase the response buffer to prevent concurrent page execution.",
         "Switch the value to true because Pages 4.0 retains only that value."],
        "Pages 4.0 removes the isThreadSafe attribute entirely. Remove it and address any unsafe shared state in the page or supporting code. Neither keeping the old value, changing its name, nor switching it to true makes a removed attribute valid.",
        "https://jakarta.ee/specifications/pages/4.0/", ["jakarta-pages-four-migration"])

    add(4, 0, "suppressed-close-exception", "trace",
        "In Java 17, what does this program print?\n```java\nclass Main {\n  static class R implements AutoCloseable {\n    public void close() { throw new IllegalStateException(\"close\"); }\n  }\n  public static void main(String[] args) {\n    try (R r = new R()) { throw new IllegalArgumentException(\"body\"); }\n    catch (Exception e) {\n      System.out.print(e.getMessage() + \":\" + e.getSuppressed()[0].getMessage());\n    }\n  }\n}\n```",
        "`body:close`", ["`close:body`", "`body:body`", "An ArrayIndexOutOfBoundsException occurs because no exception is suppressed."],
        "The exception from the try body is primary, and the exception from close is recorded as suppressed. The output is body:close. Reversing the strings incorrectly makes the close failure primary; repeating body ignores the close failure. Both unchecked exceptions are legal here.",
        JLS + "jls-14.html#jls-14.20.3", ["try-with-resources-suppression"])
    add(4, 1, "money-decimal-contract", "design",
        "A billing rule calculates a decimal tax amount and rounds once to two decimal places using HALF_UP. Inputs arrive as decimal strings. Which implementation best preserves that stated rule?",
        "Parse BigDecimal from the strings, perform decimal arithmetic, then apply the specified scale and rounding at the rule boundary.",
        ["Parse double first, construct BigDecimal from that double, and expect the original decimal value to be restored.",
         "Parse BigDecimal from strings and round each intermediate amount to two decimal places.",
         "Parse BigDecimal from strings and use HALF_EVEN when rounding the final amount."],
        "Constructing BigDecimal directly from decimal strings preserves the input values. Apply HALF_UP once at the required boundary. Constructing it from a double can preserve a binary approximation, while rounding each intermediate value or choosing another rounding mode changes the stated business rule.",
        "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/math/BigDecimal.html", ["decimal-money", "rounding-policy"])
    add(4, 2, "executor-nested-wait", "debug",
        "A Java fixed pool has four workers. Four parent tasks each submit a child to that same pool and immediately wait on child.get(). No timeout or cancellation exists. Why can all work stop?",
        "Every worker can be occupied by a parent waiting for queued child tasks that have no available worker.",
        ["The executor requires synchronized on the Future before any child can begin.",
         "The queue rejects every child because submitting a task from another task is prohibited.",
         "The executor shuts down automatically when all its workers call Future.get."],
        "All four workers can be held by parents whose children are queued behind them. The children cannot run until a worker becomes free. This is thread starvation caused by a dependency cycle, not a monitor-lock requirement, queue rejection, or an implicit executor shutdown.",
        "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html", ["executor-thread-starvation"], "hard")
    add(4, 3, "jdeps-internal-api-audit", "apply",
        "Before a JDK upgrade, a team needs a static report of compiled application references to JDK internal APIs. Which tool invocation targets that evidence?",
        "Run jdeps --jdk-internals on the application artifacts and review dependencies separately.",
        ["Run jdeprscan to list deprecated APIs and treat that as the internal-API report.",
         "Run jdeps --list-deps and treat every listed module as a JDK-internal dependency.",
         "Run javap -public and treat public application members as proof of supported JDK use."],
        "jdeps --jdk-internals reports statically visible dependencies on internal JDK APIs. Dependency listing alone does not classify internal use, jdeprscan reports deprecated APIs, and javap disassembles classes. Reflection and runtime-loaded dependencies still need separate investigation.",
        "https://docs.oracle.com/en/java/javase/17/docs/specs/man/jdeps.html", ["jdeps-internal-apis"])
    add(4, 4, "virtual-thread-downstream-limit", "design",
        "A Java 21 standalone service replaces a 100-thread pool with a virtual-thread-per-task executor. Its partner permits only 40 concurrent requests. What should happen to the partner concurrency limit?",
        "Keep an explicit admission limit around partner calls; inexpensive threads do not increase partner capacity.",
        ["Remove the limit because virtual threads provide automatic partner backpressure.",
         "Replace the concurrency limit with a timeout on every partner call.",
         "Limit HTTP connections to 40 even though each connection permits concurrent multiplexed calls."],
        "Virtual threads make waiting cheaper but do not raise the partner's capacity. Keep a separate limit on simultaneous partner calls. Timeouts, an HTTP connection count that permits multiplexing, and thread availability do not by themselves enforce the required concurrency ceiling.",
        "https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html", ["virtual-thread-admission-control"])

    add(5, 0, "null-unrelated-overloads", "debug",
        "Java 17 declares void send(String value) and void send(Integer value) in the same class. Why does send(null) fail to compile?",
        "Both overloads are applicable and neither parameter type is more specific than the other.",
        ["The first declared overload wins, but its result cannot be assigned.",
         "Integer wins through boxing, but converting null to int fails during compilation.",
         "The runtime type of null is needed to select the overriding method."],
        "null is compatible with both String and Integer, but neither class is a subtype of the other. There is no most-specific overload. Source order does not break the tie, and runtime dispatch or unboxing cannot rescue a call that fails overload resolution.",
        JLS + "jls-15.html#jls-15.12.2.5", ["overload-null-ambiguity"])
    add(5, 1, "generic-interface-dual-role", "apply",
        "Java 17 declares Sink<T> with void accept(T item). TextSink extends Sink<String>; NumberSink extends Sink<Integer>. A proposed adapter implements both TextSink and NumberSink. Which design respects Java's type rules?",
        "Expose separate typed adapter objects; one class cannot inherit Sink with both different type arguments.",
        ["Implement both accept overloads; that always permits inheriting the two Sink parameterizations.",
         "Mark the adapter final so erasure no longer applies to its implemented interfaces.",
         "Add @SuppressWarnings to convert conflicting generic inheritance into a legal declaration."],
        "A class cannot inherit two different parameterizations of the same generic interface. Separate typed adapter objects preserve both roles. Adding overloaded accept methods, marking the class final, or suppressing warnings does not make the conflicting inheritance legal.",
        JLS + "jls-8.html#jls-8.1.5", ["generic-interface-conflicting-parameterizations"])
    add(5, 2, "binary-method-descriptor", "debug",
        "A client was compiled against library method public Number amount(). A replacement library changes that method to public Integer amount(), without retaining a bridge or old method. The old client is not recompiled. What failure can occur on invocation?",
        "NoSuchMethodError, because the old binary references the method descriptor returning Number.",
        ["No failure is possible because every covariant source change preserves existing binary descriptors.",
         "ClassCastException before linkage because Integer does not extend Number.",
         "The JVM recompiles the client automatically against the new return type."],
        "The old binary references a method descriptor with Number as its return type. Removing that descriptor can produce NoSuchMethodError. Integer being a subtype helps source-level assignments but does not retain the old method. A cast failure would occur later, and the JVM does not recompile clients automatically.",
        JLS + "jls-13.html#jls-13.4.15", ["binary-method-compatibility"], "hard")
    add(5, 3, "equality-inheritance-symmetry", "debug",
        "Money.equals accepts any instanceof Money and compares amount. Voucher extends Money but its equals accepts only Voucher and also compares store. For equal amounts, money.equals(voucher) is true and voucher.equals(money) is false. Which contract test exposes the defect?",
        "Assert symmetry across base and subtype instances, then redesign equality or use composition.",
        ["Assert only that two identical references have identical hash codes.",
         "Assert that toString includes the store so collection lookups can distinguish values.",
         "Assert that Voucher has a serialVersionUID to make equality symmetric."],
        "The two calls disagree when their operands are reversed, violating symmetry. Hash-code equality is a separate requirement and cannot repair this defect. String representations and serialization metadata do not participate in the equals contract.",
        "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html#equals(java.lang.Object)", ["equality-symmetry-inheritance"])
    add(5, 4, "sealed-exhaustive-domain", "design",
        "A Java 21 application models PaymentResult as a sealed interface permitting Approved and Declined records. A switch expression handles both without default. After adding Pending to permits and recompiling the whole application, what useful check does the compiler provide?",
        "It rejects the now-incomplete switch until Pending is handled or another exhaustive alternative is provided.",
        ["It silently treats Pending as Declined because that was the last existing case.",
         "It prevents any future subtype from being added even when the interface source is edited.",
         "It makes every switch exhaustive regardless of its cases because records are immutable."],
        "The compiler uses the permitted subclasses to check exhaustiveness. Adding Pending makes the recompiled switch incomplete. No existing case is selected automatically, and editing a sealed hierarchy is allowed. Record immutability does not provide a missing case; separately deployed old binaries need their own compatibility analysis.",
        "https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.11.1.1", ["sealed-exhaustive-switch"])

    add(6, 0, "decorator-retry-metric-order", "trace",
        "RetryGateway calls its delegate until success, at most three attempts. MetricsGateway increments a counter once per invocation and calls its delegate once. The raw gateway fails twice then succeeds. In MetricsGateway(RetryGateway(raw)), what does the metrics counter record for one client call?",
        "One invocation; placing MetricsGateway inside RetryGateway would record three.",
        ["Three invocations; decorator order never affects observed calls.",
         "Zero invocations because retry hides the outer decorator.",
         "Two invocations because metrics count only failed attempts."],
        "The outer metrics decorator is entered once; the retry decorator performs all three raw attempts inside that call. Moving metrics inside retry would count each attempt. Counts of two or zero would require failure-only counting or bypassing the metrics wrapper, neither of which is specified.",
        "https://docs.oracle.com/javase/8/docs/api/java/io/FilterInputStream.html", ["decorator-order", "retry-observability"])
    add(6, 1, "visitor-change-axis", "design",
        "A reporting engine has a stable, application-owned hierarchy of document node types. New operations such as export, validation, and cost estimation arrive frequently. The team accepts updating each visitor if a new node type is introduced. Which pattern matches that change tradeoff?",
        "Visitor: keep each operation in a visitor with a visit method for each concrete node type.",
        ["Strategy: select one interchangeable calculation without type-specific visitor dispatch.",
         "Composite: organize nodes into a tree while implementing every new operation on each node class.",
         "Decorator: add a wrapper for each operation while leaving node-type dispatch unspecified."],
        "Visitor groups each operation over the known node types, making new operations straightforward. Adding a node type requires visitor updates, which the scenario accepts. A strategy chooses an algorithm, a composite organizes a tree, and a decorator wraps behavior; none provides the same explicit operation-by-node dispatch structure.",
        "https://docs.oracle.com/javase/8/docs/api/javax/lang/model/element/ElementVisitor.html", ["visitor-change-axis"])
    add(6, 2, "adapter-anti-corruption", "design",
        "A payment provider SDK exposes vendor status codes and checked exceptions. A second provider must be introduced while domain services keep a stable PaymentPort interface and domain outcomes. Where should vendor translation live?",
        "In a provider adapter implementing PaymentPort, with explicit status and error mappings.",
        ["In every domain service so each call site interprets vendor codes independently.",
         "In the PaymentPort signature by exposing both providers' concrete response classes.",
         "In a single generic exception handler that discards provider-specific status details."],
        "The provider adapter translates the vendor contract into the stable domain port. Mapping in every service duplicates provider knowledge; exposing SDK response types leaks that knowledge through the port. A shared catch-all response mapper also lacks the provider-specific meaning needed for reliable translation.",
        "https://alistair.cockburn.us/hexagonal-architecture/", ["provider-adapter", "domain-port"])
    add(6, 3, "builder-domain-invariant", "apply",
        "A report request has optional filters and requires startDate <= endDate. A fluent Builder offers setters in any order. Where should it enforce the complete cross-field invariant before publishing an immutable request?",
        "In build() or the constructed value's validated constructor, after the required inputs are available.",
        ["Immediately after construction, by asking each caller to invoke a validation method.",
         "Only in the first setter, before the other date is known.",
         "In each consumer independently, allowing the builder to publish invalid values."],
        "build() or the validated value constructor sees the complete candidate request and can reject an invalid date range before publication. Per-field checks cannot establish the relationship when the other field is unset. Relying on consumers or post-construction validation allows invalid immutable values to escape.",
        "https://docs.oracle.com/en/java/javase/17/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html#build()", ["builder-validation-boundary"])
    add(6, 4, "ai-adapter-policy-boundary", "design",
        "An application adds two generative-AI providers to suggest claim categories. Suggestions must pass existing deterministic eligibility rules before affecting a claim. Which architecture keeps provider changes and nondeterministic output out of domain policy?",
        "Expose a suggestion port with provider adapters; validate suggestions and apply eligibility rules in the domain workflow.",
        ["Validate the provider's response schema and treat every well-formed category as eligible.",
         "Let each SDK write directly to claim tables to minimize the number of boundaries.",
         "Return vendor response types from every domain method and duplicate rule checks in each adapter."],
        "Provider adapters translate external suggestions, while the domain workflow validates input and applies eligibility rules. A valid output schema does not establish eligibility. Direct database writes bypass the domain boundary, and rules duplicated in vendor adapters can diverge.",
        "https://alistair.cockburn.us/hexagonal-architecture/", ["ai-provider-adapters", "domain-policy-boundary"], "hard")

    add(7, 0, "ejb-independent-audit-commit", "apply",
        "A container-managed EJB REQUIRED checkout method calls a separate audit EJB through its business proxy. Audit uses REQUIRES_NEW and commits successfully. Checkout then rolls back. Assuming no later failure, what happens to the audit row?",
        "It remains committed because the audit method used an independent transaction.",
        ["It rolls back because the inner method uses a savepoint in the checkout transaction.",
         "It remains pending because the audit commit waits for checkout's final outcome.",
         "It is rolled back when the audit bean instance is returned to its pool."],
        "REQUIRES_NEW commits the audit transaction independently while the checkout transaction is suspended. Rolling back checkout does not undo the completed audit commit. A savepoint would remain part of the outer transaction; neither delayed commit nor bean-pool lifecycle is the rule here.",
        EJB + "#transaction-attributes", ["ejb-requires-new-audit"])
    add(7, 1, "ejb-singleton-read-lock", "debug",
        "A @Singleton EJB uses container-managed concurrency. Its refresh() method has @Lock(READ) and mutates a shared HashMap. Multiple callers run refresh concurrently and corrupt state. Which annotation-level repair matches this mutation?",
        "Use @Lock(WRITE) for the mutating method so it excludes other container-managed invocations on the instance.",
        ["Keep @Lock(READ); READ means the method reads and then exclusively writes.",
         "Mark the map reference final to make compound mutations thread-safe.",
         "Add @Asynchronous so concurrent mutations cannot overlap."],
        "A READ lock permits concurrent invocations, including the unsafe concurrent mutations in this example. WRITE excludes other container-managed invocations on that singleton instance. A final reference does not make the map immutable, and asynchronous execution does not serialize access. The lock is not cluster-wide.",
        EJB + "#singleton-session-beans", ["ejb-singleton-locks"])
    add(7, 2, "ejb-async-transaction-context", "apply",
        "An EJB caller has an active transaction and invokes another EJB's @Asynchronous method through its business interface. That async method uses REQUIRED. Which transaction context should its business work use?",
        "A new transaction for the asynchronous invocation; the caller's transaction is not propagated.",
        ["The caller's transaction, kept open until every asynchronous method completes.",
         "No transaction because REQUIRED is ignored on all asynchronous EJB methods.",
         "The caller's transaction only if the caller later waits on the returned Future."],
        "The caller's transaction is not propagated to an asynchronous EJB invocation. REQUIRED starts a transaction for that invocation. This is neither a shared caller transaction nor a transaction-free execution. Waiting on a returned Future also does not merge the two transaction boundaries.",
        EJB + "#asynchronous-method-invocation", ["ejb-async-transactions"], "hard")
    add(7, 3, "ejb-application-exception-rollback", "debug",
        "A CMT EJB updates a row and throws a checked business exception annotated @ApplicationException(rollback=false). The transaction was not otherwise marked rollback-only. A test expects automatic rollback. Which correction aligns the business failure with that expectation?",
        "Declare rollback=true for that application exception or explicitly mark the transaction rollback-only where appropriate.",
        ["Keep rollback=false because every checked exception forces CMT rollback.",
         "Catch and ignore the exception in the client to force the server transaction to roll back.",
         "Change the bean from stateless to stateful without changing transaction semantics."],
        "An application exception with rollback=false does not mark the transaction for rollback. Set rollback=true or mark the transaction rollback-only at the correct boundary. Client-side catching occurs too late to change that rule, and bean scope does not select rollback semantics.",
        EJB + "#application-exceptions", ["ejb-application-exceptions"])
    add(7, 4, "ejb-lite-mdb-portability", "design",
        "A modernization plan moves an application containing message-driven beans to a runtime whose declared guarantee is EJB Lite only. What must be checked before approving this target?",
        "Whether the runtime supplies message-driven bean support beyond EJB Lite, or the messaging consumer must be redesigned.",
        ["Nothing; EJB Lite guarantees every message-driven bean service from the full EJB specification.",
         "Only whether the class is renamed from javax to jakarta; annotations supply container services themselves.",
         "Whether the MDB has a public constructor, which makes any servlet-only engine an EJB container."],
        "EJB Lite does not require message-driven beans. Confirm that the target provides the necessary extension or choose another consumer design. Having Messaging APIs, compatible annotation names, or servlet support does not itself provide an MDB container.",
        EJB + "#enterprise-beans-lite", ["ejb-lite-mdb-capabilities"])

    add(8, 0, "java-nine-optional-stream", "trace",
        "In Java 9, what does this code print?\n```java\njava.util.List<java.util.Optional<String>> values = java.util.List.of(\n    java.util.Optional.of(\"A\"), java.util.Optional.empty(),\n    java.util.Optional.of(\"BC\"));\nlong count = values.stream().flatMap(java.util.Optional::stream).count();\nSystem.out.print(count);\n```",
        "`2`", ["`3`", "`1`", "NoSuchElementException is thrown for the empty Optional."],
        "Optional.stream contributes one element for each present value and none for an empty value. There are two present Strings, so count is 2. A count of 3 would count the containers or characters; a count of 1 would discard a present value. Empty optionals do not throw here.",
        JAVA9 + "java/util/Optional.html#stream--", ["java-nine-optional-stream"])
    add(8, 1, "java-nine-transitive-api", "apply",
        "Module billing.api exports a package whose public method returns a type from money.api. Client modules require billing.api and should be able to use that exposed money type without separately declaring its dependency. money.api exports the type's package. Which directive belongs in billing.api?",
        "requires transitive money.api;",
        ["requires static money.api;", "opens money.api;", "exports money.api;"],
        "requires transitive makes money.api readable to consumers that read billing.api. requires static describes an optional runtime dependency and does not express this transitive API contract. opens and exports refer to this module's packages, not a dependency module's name.",
        "https://docs.oracle.com/javase/specs/jls/se9/html/jls-7.html#jls-7.7.1", ["jpms-transitive-readability"])
    add(8, 2, "java-nine-qualified-opens", "debug",
        "A named module exports com.acme.model. A framework module named mapper.core tries deep reflection on private model fields and gets an access error. The team wants to grant that framework access without opening every package to everyone. Which directive fits?",
        "opens com.acme.model to mapper.core;",
        ["exports mapper.core to com.acme.model;", "requires transitive mapper.core;", "provides com.acme.model with mapper.core;"],
        "A qualified opens grants mapper.core deep reflective access to com.acme.model. Exporting a package only exposes its public API; requires adds readability rather than private-member access. A provides directive registers a service implementation and is unrelated to reflective access.",
        "https://docs.oracle.com/javase/specs/jls/se9/html/jls-7.html#jls-7.7.2", ["jpms-qualified-opens"])
    add(8, 3, "jlink-bind-provider", "debug",
        "A Java 9 modular application uses ServiceLoader. The consumer declares uses, and a provider module on the module path declares provides. A jlink image rooted only at the consumer omits the otherwise unreferenced provider. Which option can include observable service providers and their dependencies during linking?",
        "--bind-services",
        ["--strip-debug", "--no-header-files", "--compress=2"],
        "--bind-services resolves observable provider modules and their dependencies during image linking. The provider still needs a correct provides declaration and must be available on the module path. Debug stripping, header removal, and compression change image contents or size, not service resolution.",
        "https://docs.oracle.com/javase/9/tools/jlink.htm", ["jlink-service-binding"])
    add(8, 4, "java-nine-to-seventeen-encapsulation", "design",
        "A library used on Java 9 relies on reflective access to private JDK implementation fields. During migration to Java 17 it fails with InaccessibleObjectException. Which long-term response best addresses modern JDK encapsulation?",
        "Upgrade or replace the library to use supported APIs, using narrowly scoped opens only as a documented migration bridge if needed.",
        ["Set --illegal-access=permit and assume Java 17 restores Java 9's relaxed behavior indefinitely.",
         "Export the JDK package with --add-exports and expect that to permit private-field reflection.",
         "Call setAccessible(true) without opening the JDK package and rely on the library's previous behavior."],
        "Java 17 strongly encapsulates JDK internals. Updating the dependency to supported APIs addresses the underlying compatibility problem. --illegal-access no longer restores the older relaxed behavior; exports does not grant private reflection, and setAccessible still obeys module access restrictions. A targeted opens can be a temporary migration measure.",
        "https://openjdk.org/jeps/403", ["jdk-strong-encapsulation"], "hard")

    add(9, 0, "jms-client-ack-session-scope", "apply",
        "A standalone Jakarta Messaging client uses a non-transacted CLIENT_ACKNOWLEDGE session and synchronously receives messages A and B. It calls B.acknowledge(). With no earlier acknowledgement, which messages does that acknowledge?",
        "Both A and B, because acknowledgement covers messages consumed by that session.",
        ["Only B, because acknowledge always applies only to the receiver object.",
         "Neither message until Session.commit is called in this non-transacted session.",
         "Every message on the destination, including those delivered to other sessions."],
        "CLIENT_ACKNOWLEDGE covers messages consumed by this session, so acknowledging B also acknowledges A. It is not per-message or destination-wide. Session.commit belongs to transacted sessions and is not the completion mechanism for the non-transacted session in this question.",
        JMS + "#reliability", ["jms-client-acknowledge-scope"])
    add(9, 1, "jms-shared-durable-fanout", "design",
        "Billing and Analytics must each receive every retained topic event. Each service has multiple competing workers and must survive disconnects. How should shared durable subscriptions be arranged?",
        "Use a distinct shared durable subscription per service and let each service's workers share only its subscription.",
        ["Put every worker from both services in one shared durable subscription so every worker receives every event.",
         "Use one queue for both services and assume every queued message is copied to both.",
         "Use non-durable subscribers and assume disconnected consumers retain the same delivery guarantee."],
        "Each subscription receives its own topic stream; workers sharing a subscription divide that stream. Separate subscriptions for Billing and Analytics therefore give each service a copy. One shared subscription or one competing-consumer queue divides work between the services, and non-durable subscriptions do not retain disconnected subscribers' messages.",
        JMS + "#publish-subscribe", ["jms-shared-durable-subscriptions"], "hard")
    add(9, 2, "jms-atomic-consume-produce", "design",
        "A standalone Jakarta Messaging worker receives from queue A and sends a transformed message to queue B using the same locally transacted Session and provider. There are no database or external effects. A validation step fails after send but before commit, and the worker calls rollback. Which result follows?",
        "The send is rolled back and the consumed message is recovered for redelivery subject to provider redelivery policy.",
        ["The send remains committed while only the receive rolls back, even though both use the same transacted Session.",
         "The receive is permanently acknowledged because calling send implicitly commits the Session.",
         "Rollback has no effect unless the application adds an XA transaction manager for these same-session operations."],
        "The same local messaging transaction includes the receive from A and send to B. Rollback cancels the send and recovers the received message, subject to redelivery policy. send does not implicitly commit, and XA is unnecessary for this single-session messaging boundary. Separate database work would require additional coordination.",
        JMS + "#transactions", ["jms-atomic-consume-produce"], "hard")
    add(9, 3, "jms-selector-property-type", "debug",
        "A producer calls setStringProperty(\"priorityCode\", \"7\"). A consumer selector is priorityCode = 7, using a numeric literal, and receives no matches. Which fix aligns the property with this numeric selector?",
        "Publish priorityCode with setIntProperty(\"priorityCode\", 7).",
        ["Keep the String property; selectors must convert all numeric-looking strings automatically.",
         "Set JMSPriority to 7 and assume it creates a property named priorityCode.",
         "Move the value into the text body because selectors parse body fields automatically."],
        "The selector compares a numeric literal with a property, so publish that property as an integer. Selector evaluation does not convert a String to a number as typed message getters may do. JMSPriority is a different header, and body content is not automatically a selector property.",
        JMS + "#message-selectors", ["jms-selector-types"])
    add(9, 4, "jms-delivery-delay-version", "apply",
        "A Jakarta Messaging 3.1 producer must defer an event's earliest delivery by 30 seconds using a standard API. Which setting expresses that requirement without sleeping in the request thread?",
        "Set the producer's delivery delay to 30,000 milliseconds before sending.",
        ["Set time-to-live to 30,000 milliseconds; expiry delays the start of delivery.",
         "Set JMSPriority to 0; the specification guarantees a 30-second delay for low priority.",
         "Use a vendor-only header because standard delayed delivery was never added after JMS 1.1."],
        "A delivery delay of 30,000 milliseconds sets the earliest delivery time. A time-to-live controls expiry, and priority affects ordering rather than a fixed delay. Standard delivery delay is available in Messaging 3.1, so a vendor-only scheduling header is unnecessary. Exact dispatch at 30 seconds is not guaranteed.",
        JMS, ["jms-delivery-delay"])

    return {
        "schema_version": 1,
        "id": "jakarta-competency-exam",
        "title": "Jakarta Competency Exam",
        "description": "50 original enterprise Java scenarios across ten topics and five knowledge areas. "
                       "Independent competency practice; not affiliated with or validated by Accenture. "
                       "Java 17 unless a question specifies Java 9 or 21; framework and Jakarta versions are stated where relevant.",
        "subject": "Java Enterprise / Jakarta EE",
        "difficulty": "hard",
        "lessons": [],
        "tests": [{
            "id": "jakarta-competency-exam-test",
            "title": "Jakarta Competency Exam",
            "description": "Mixed-topic assessment of implementation, architecture, deployment, tools, and modernization. "
                           "Select all 50 questions for the full practice exam; this is not an official scoring benchmark.",
            "difficulty": "hard",
            "questions": questions,
        }],
    }
