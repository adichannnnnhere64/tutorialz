"""Integrated enterprise scenarios with competing, plausible design choices."""
from question_bank import assessment, choice


def questions(sources):
    result = {}

    def add(category, objective, topics, prompt, answer, wrong, explanation, source=None):
        q = choice(f"ee-advanced-{objective}", prompt, answer, wrong, explanation,
                   topics[0].replace("-", " "), source or sources[category],
                   assessment(f"ee-{objective}", "design", *topics), "hard")
        result.setdefault(category, []).append(q)

    add("platform", "migrate-api-and-provider-together", ["the-jakarta-namespace", "specification-compatibility"],
        "An application changes its Servlet imports from javax.servlet to jakarta.servlet but keeps an older server and a dependency compiled against javax.servlet.Filter. Deployment fails. Which migration plan addresses the type boundary?",
        "Use a compatible Jakarta server and migrate or replace dependencies so their API types match the application's target version.",
        ["Bundle both Servlet API jars and cast between javax.servlet.Filter and jakarta.servlet.Filter.",
         "Rename imports in application source only; the container rewrites every dependency at runtime.",
         "Mark the old filter class public so it implements both unrelated interfaces."],
        "The namespace change produces different Java types. Source changes, dependent libraries, and the runtime must agree on the target APIs; merely adding both jars does not adapt implementations.")
    add("platform", "verify-profile-before-portable-deployment", ["jakarta-ee-profiles", "portable-deployment"],
        "A service uses a Jakarta API outside its selected runtime profile. It worked on a development server that supplied an extension. Operations needs deployment across multiple compatible vendors. Which acceptance criterion establishes portability?",
        "Declare a profile providing every required API and test deployment on conforming implementations of that profile.",
        ["Require every vendor to support the development server's extension because it uses a jakarta package.",
         "Bundle an API jar and assume the missing container service is now implemented.",
         "Check only that the application compiles against the newest API artifacts."],
        "API availability depends on the chosen specification profile and implementation. An API jar supplies types, while container services require a compatible runtime implementation.")
    add("servlet", "bound-async-request-work", ["async-servlet-processing", "bounded-task-queues", "request-scope"],
        "An endpoint starts asynchronous processing, then submits slow exports to an unbounded executor. Under load, worker threads stay busy and queued requests exhaust memory. What addresses the remaining bottleneck while keeping per-request data isolated?",
        "Use bounded managed execution with admission limits, explicit timeout/completion paths, and per-request task data.",
        ["Keep the queue unbounded; releasing servlet threads guarantees bounded memory.",
         "Store the current request in a servlet instance field and use one task for all callers.",
         "Create an unrestricted new thread for every export and disable async timeouts."],
        "Async processing frees the original request thread but does not bound outstanding work. Capacity limits and rejection behavior control load; request-specific data must not be stored in shared servlet fields.")
    add("servlet", "handle-failure-after-commit", ["response-commitment", "exception-mapping"],
        "A streaming response has flushed a 200 status and part of its body. A later database read fails. The handler attempts sendError(500). Which design accounts for the actual response boundary?",
        "Validate what can be validated before committing; after commitment, terminate or signal failure according to the streaming protocol and record the error.",
        ["Reset the committed response and replace all bytes already received by the client.",
         "Set the status to 500 after flushing; clients always use the last status assigned.",
         "Forward to an error page after commitment so it can replace the original headers."],
        "Once committed, the response status and headers cannot be replaced. A streaming API needs a defined partial-failure policy; preflight checks reduce but cannot eliminate failures during streaming.")
    add("rest", "combine-http-and-database-concurrency", ["conditional-requests", "optimistic-locking"],
        "Two clients GET version 5 of an entity, then both PUT updates with If-Match for version 5. Each HTTP handler reads version 5 before either commits. Which design prevents both writes from silently succeeding?",
        "Enforce the precondition and a version check atomically with the database update; map a stale version to a conflict response.",
        ["Compare If-Match only before beginning the transaction, then update without a version predicate.",
         "Generate a fresh ETag after every response while allowing both unversioned writes.",
         "Make the endpoint synchronized on one server instance to guarantee safety across all cluster nodes."],
        "A separate read-and-compare has a race. A database version predicate or optimistic lock makes the check effective at write time, so a concurrent loser cannot overwrite unseen changes.")
    add("rest", "persist-idempotency-with-result", ["idempotent-updates", "atomic-commit"],
        "A POST creates an order, commits, then loses its HTTP response. The client retries with the same idempotency key. Multiple nodes may handle retries. Which design prevents a second order while returning a consistent result?",
        "Persist the key, request identity, and result with the order under a unique constraint; replay the recorded result and reject conflicting reuse of the key.",
        ["Remember the last key only in the servlet's instance field.",
         "Generate a new order ID on each retry because POST requests cannot be deduplicated.",
         "Check for the key outside the transaction without a uniqueness constraint."],
        "The key and business effect need a durable, atomic boundary. A unique key handles races across nodes, and request identity prevents the same key from being reused for a different operation.")
    add("cdi", "qualify-implementation-with-correct-lifetime", ["type-safe-injection", "qualifiers", "bean-scopes"],
        "CDI discovers two implementations of Pricing. Checkout needs the regional implementation, while each calculation uses request-specific customer data. Which change selects the implementation without sharing customer state across requests?",
        "Use a matching qualifier at the bean and injection point, and keep customer data in parameters or an appropriate request context.",
        ["Rename the regional class alphabetically first and store the current customer in an application-scoped mutable field.",
         "Mark both implementations as the default and rely on discovery order to choose one.",
         "Construct the regional bean with new and expect CDI to inject all its fields automatically."],
        "Qualifiers disambiguate type-safe resolution. Selection and lifetime are separate concerns; a globally shared field is not a safe home for per-request customer data.")
    add("cdi", "transaction-observer-is-not-durable-outbox", ["events", "outbox-pattern"],
        "An AFTER_SUCCESS transactional CDI observer sends an event to a remote system after an order commits. A process crash between commit and the send loses the notification. Delivery must survive restarts. What closes this gap?",
        "Store an outbox row in the order transaction and let a retrying publisher deliver it with an idempotent consumer.",
        ["Use an after-success observer alone; its callbacks are durably replayed after every crash.",
         "Send before committing and assume a later rollback cancels the remote side effect.",
         "Catch send failures in memory and clear them during shutdown."],
        "Transaction-phase observation controls when a callback runs; it is not a durable delivery log. Persisting delivery intent with the order survives the failure gap, while retries require duplicate handling.",
        "https://microservices.io/patterns/data/transactional-outbox.html")
    add("persistence", "page-parents-with-bounded-fetches", ["lazy-relationships", "n-plus-one-queries", "pagination"],
        "A paged orders endpoint serializes lazy line items after closing the persistence context. Making every association eager loads huge graphs. The endpoint needs predictable page sizes and query counts. Which plan best fits?",
        "Select a stable page of order IDs, fetch only the required data for those IDs within the transaction, and return DTOs in the requested order.",
        ["Enable eager loading for all relationships globally and keep the same serialization path.",
         "Join-fetch every collection with pagination and assume every provider preserves parent page sizes.",
         "Catch lazy-loading failures during serialization and return incomplete data without signaling it."],
        "An explicit fetch plan keeps required reads within the context and avoids unbounded graph loading. Paging parents before fetching collection data avoids row multiplication changing parent page semantics.")
    add("persistence", "retry-conflict-from-fresh-state", ["optimistic-locking", "persistence-context"],
        "Two inventory reservations update the same versioned row. One transaction loses with an optimistic-lock failure. Stock must never go below zero. If an automatic retry is allowed, what must it do?",
        "Start a fresh transaction, reload current stock, re-evaluate the reservation rule, and retry only within a bounded policy.",
        ["Keep using the failed transaction and flush the same stale entity until it succeeds.",
         "Remove the version field during retries to avoid further conflicts.",
         "Overwrite the database with the original requested final value without rechecking stock."],
        "The original decision used stale state, and the failed transaction is not a valid retry boundary. Re-evaluation against fresh state preserves the business invariant; bounded retries avoid livelock under contention.")
    add("transactions", "checked-exception-rolls-back-use-case", ["rollback-rules", "transactional-tests"],
        "A CDI method annotated @Transactional writes two rows, then throws checked PaymentRejectedException. The use case requires both writes to roll back, but they commit under the default rules. Which fix and test address the requirement?",
        "Configure rollbackOn for PaymentRejectedException and assert the absence of both rows from a separate transaction after the failed call.",
        ["Catch and ignore the exception inside the method; all handled failures automatically roll back.",
         "Assert only that the exception was thrown; this proves no database writes committed.",
         "Move one write into REQUIRES_NEW so both writes always share rollback fate."],
        "Checked exceptions do not by default mark a Jakarta @Transactional transaction for rollback. An explicit rollback rule plus an independent persisted-state assertion tests the required outcome.")
    add("transactions", "compensate-independent-service-steps", ["saga-compensation", "two-phase-commit"],
        "A booking workflow reserves inventory and charges a remote payment API. Neither service participates in a shared XA transaction. The payment succeeds but final booking creation fails. Which recovery design fits these boundaries?",
        "Persist workflow progress and run retryable, idempotent compensations such as releasing the reservation and refunding the payment.",
        ["Roll back the local database transaction and assume the remote charge disappears.",
         "Add @Transactional around the HTTP calls so every remote API automatically joins XA.",
         "Keep the database lock forever until an operator manually edits all services."],
        "Independent commits cannot be undone by a local rollback. Compensation is a separate business operation that can itself fail and needs durable progress, retries, and idempotency.",
        "https://microservices.io/patterns/data/saga.html")
    add("security", "rotate-session-and-check-browser-intent", ["session-fixation-defense", "csrf-protection"],
        "A browser application uses a session cookie for authenticated writes. Login succeeds using a pre-existing session ID, and a third-party page can submit its transfer form. Which pair addresses both attack paths?",
        "Rotate the session ID after authentication and validate an anti-CSRF token for the state-changing request.",
        ["Use HTTPS alone and keep the pre-login session ID and unchecked form submissions.",
         "Change transfer from POST to GET so browser navigation proves user intent.",
         "Hide the transfer button and retain the original session ID."],
        "Rotating session identity limits fixation; validating browser request intent addresses CSRF. Transport encryption and hidden UI controls do not by themselves establish that intent.")
    add("security", "authorize-each-tenant-resource", ["declarative-authorization", "principal-propagation", "least-privilege"],
        "A REST endpoint requires the user role and loads invoices by an ID supplied in the URL. A logged-in user can guess another tenant's invoice ID. Which additional boundary is needed?",
        "Authorize the specific invoice against the authenticated principal's tenant or permissions before returning it, preferably constraining the query as well.",
        ["Rely on the user role alone because successful authentication grants every invoice.",
         "Change numeric IDs to UUIDs and remove authorization checks.",
         "Trust a tenant header supplied by the client without binding it to the principal."],
        "A role check does not establish access to every object. Resource authorization must bind the requested data to trusted identity and permissions; hard-to-guess IDs are not an authorization boundary.")
    add("messaging", "deduplicate-with-business-transaction", ["at-least-once-delivery", "acknowledgment", "atomic-commit"],
        "A consumer applies a database credit and crashes before acknowledging its message. Redelivery is expected. Which design prevents the credit from being applied twice, even with concurrent consumers?",
        "Insert a unique processed-operation ID and apply the credit in the same database transaction; acknowledge only after commit and safely acknowledge known duplicates.",
        ["Record the operation ID in memory after applying the credit.",
         "Acknowledge before starting the database work so crashes cannot cause replay.",
         "Check a processed table without a unique constraint, then insert the marker in a later transaction."],
        "The durable marker and business effect need a single atomic boundary, with uniqueness resolving races. Early acknowledgment risks lost work; an in-memory marker cannot survive restart.")
    add("messaging", "preserve-order-with-parallel-consumers", ["message-ordering", "backpressure"],
        "Account events carry sequence numbers. Adding consumers raises throughput but allows event 12 for an account to complete before event 11. Different accounts may process independently. Which design preserves the needed ordering while retaining useful parallelism?",
        "Route each account consistently to an ordered processing lane and enforce sequence/duplicate checks at the consumer.",
        ["Process every message concurrently and assume dequeue order guarantees completion order.",
         "Remove sequence numbers because queues make all processing globally ordered.",
         "Increase retry counts without coordinating events for the same account."],
        "Completion order can diverge under concurrency. Key-based routing preserves per-account serialization while independent accounts remain parallel; sequence checks handle replay and gaps.")
    add("validation", "close-uniqueness-validation-race", ["database-constraints", "validation-boundaries"],
        "Two registration requests both pass a check that an email is unused, then both insert it. The product requires unique emails, including writes from other tools. Which design enforces the invariant and gives clients a useful response?",
        "Add a database uniqueness constraint and map a conflicting insert to a stable domain/API error; an early check can remain for feedback.",
        ["Move the same existence check into a Bean Validation annotation and omit the database constraint.",
         "Synchronize one application instance while allowing other nodes and tools to write freely.",
         "Retry every conflicting registration indefinitely with the same email."],
        "Application checks have a time-of-check/time-of-use race. The database constraint arbitrates concurrent writers at the storage boundary; controlled error mapping makes that enforcement usable.")
    add("validation", "combine-nested-and-cross-field-validation", ["cascaded-validation", "cross-field-validation", "validation-groups"],
        "CreateBooking contains a nested Passenger and start/end dates. Individual fields are non-null, but nested constraints are skipped and end can precede start. Update requests use different rules. Which validation plan covers these independent requirements?",
        "Cascade validation into Passenger, validate the date relationship at object/domain level, and select the intended validation groups for each workflow.",
        ["Add @NotNull to CreateBooking alone; this recursively checks every nested field and date relationship.",
         "Validate only start and end separately and assume individually valid dates imply a valid interval.",
         "Apply every update-only constraint to all create requests to avoid selecting groups."],
        "Cascading reaches nested objects, a cross-field rule checks the relationship, and groups select workflow-specific constraints. One of these mechanisms does not automatically provide the others.")
    add("concurrency", "isolate-slow-dependency-capacity", ["bulkheads", "connection-pool-sizing", "timeouts-and-retries"],
        "A slow partner API consumes every worker, including those serving healthy endpoints. The database is already at capacity, and retries multiply traffic. Which response protects unrelated work without worsening database saturation?",
        "Give the dependency a separate bounded concurrency budget, enforce timeouts and bounded safe retries, and size database concurrency from measured capacity.",
        ["Double all thread and database pools and retry every failure immediately.",
         "Remove timeouts so no request is rejected before the partner recovers.",
         "Use one unbounded queue for all endpoints so every request is eventually admitted."],
        "Isolation prevents one dependency from occupying all service capacity. Increasing concurrency beyond a bottleneck raises queueing, and uncontrolled retries amplify load rather than creating capacity.")
    add("concurrency", "cooperative-cancellation-and-durable-work", ["structured-cancellation", "managed-executors", "graceful-shutdown"],
        "An export task runs in managed execution and writes to a remote store. The request times out and Future.cancel(true) is called. The worker ignores interruption and continues writing during shutdown. What is the correct lifecycle design?",
        "Make task and I/O cancellation cooperative, set operation timeouts, define safe partial-work handling, and drain or recover durable work within a shutdown deadline.",
        ["Assume cancel(true) forcibly kills the worker and rolls back every remote write.",
         "Use Thread.stop so partially updated state cannot be observed.",
         "Ignore interruption and wait indefinitely during every deployment."],
        "Cancellation requests are not an atomic rollback of arbitrary work. The task must cooperate, blocking operations need bounds, and already-performed side effects need an explicit recovery policy.")
    return result


def course(sources):
    grouped = questions(sources)
    tests = [{"id": f"ee-advanced-{category}-test", "title": f"{category.title()} practice",
              "description": "Integrated decisions about failures, boundaries, and tradeoffs.",
              "difficulty": "hard", "questions": items} for category, items in grouped.items()]
    total = sum(len(t["questions"]) for t in tests)
    return {"schema_version": 1, "id": "ee-advanced",
            "title": "Java Enterprise and Jakarta EE — Advanced",
            "description": f"{total} integrated enterprise scenarios across ten subject areas.",
            "subject": "Java Enterprise / Jakarta EE", "difficulty": "hard", "lessons": [], "tests": tests}
