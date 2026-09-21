"""Build original practice questions grounded in the Jakarta EE specifications.

Each row contributes one recall question and one repair question. Integrated
advanced cases and OOP questions are authored separately, without variant loops.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from java_content import courses as java_courses
from advanced_content import course as advanced_course
from jakarta_competency_content import course as competency_course
from jakarta_dummy_content import course as dummy_course
from question_bank import assessment, audit, choice, preserve_revisions, slug

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "enterprise"

SOURCES = {
    "platform": "https://jakarta.ee/specifications/platform/11/",
    "servlet": "https://jakarta.ee/specifications/servlet/6.1/",
    "rest": "https://jakarta.ee/specifications/restful-ws/4.0/",
    "cdi": "https://jakarta.ee/specifications/cdi/4.1/",
    "persistence": "https://jakarta.ee/specifications/persistence/3.2/",
    "transactions": "https://jakarta.ee/specifications/transactions/2.0/",
    "security": "https://jakarta.ee/specifications/security/4.0/",
    "messaging": "https://jakarta.ee/specifications/messaging/3.1/",
    "validation": "https://jakarta.ee/specifications/bean-validation/3.1/",
    "concurrency": "https://jakarta.ee/specifications/concurrency/3.1/",
}

# category|concept|behavior|failure signal|response
FACTS = """
platform|Jakarta EE profiles|select a defined subset of platform APIs|a deployment depends on an API absent from its target profile|declare a compatible profile or deploy to a runtime that supplies that API
platform|the jakarta namespace|identifies current Jakarta APIs after the javax transition|legacy imports fail after a Jakarta EE migration|migrate imports and dependencies together to matching Jakarta artifacts
platform|portable deployment|relies on specification contracts across compatible products|application code depends on one vendor's extension|isolate vendor extensions and test against the declared profile
platform|application server services|provide managed lifecycle, security, and transactions|a manually created object has no container services|obtain the component through the container
platform|WAR packaging|packages web components and resources for deployment|a web artifact is missing runtime classes or descriptors|inspect WAR layout and dependency scope
platform|EAR packaging|groups enterprise modules with shared deployment metadata|module class loading differs from local development|define explicit module dependencies and test the assembled EAR
platform|configuration by environment|separates deploy-specific values from application logic|production credentials are embedded in source|inject configuration from the deployment environment
platform|resource injection|resolves container-managed resources|a lookup works locally but fails on the target server|verify the resource name and target server binding
platform|application lifecycle callbacks|run at managed construction and destruction boundaries|cleanup never runs for manually instantiated components|move lifecycle logic to a container-managed component
platform|specification compatibility|defines portable behavior, not identical vendor internals|a vendor-specific tuning knob changes across servers|separate portable behavior from measured vendor tuning
servlet|servlet mappings|route matching HTTP requests to a servlet|the endpoint returns 404 although the application deploys|check the context path and mapping pattern
servlet|filter chains|process matching requests before and after a target|authentication logic is skipped for one URL pattern|verify filter mappings and chain order
servlet|request scope|holds data for one HTTP request|user-specific values leak between requests|store request-specific state on the request rather than servlet fields
servlet|session scope|associates state with a browser session|users lose state when sessions expire or nodes change|define session lifetime and replication strategy explicitly
servlet|application scope|shares attributes within a web application|a shared mutable attribute races under load|protect shared state or use an appropriate managed store
servlet|async servlet processing|releases request threads while work continues|long requests exhaust the servlet worker pool|use supported asynchronous processing with a bounded executor
servlet|HTTP method semantics|distinguish safe reads from state-changing requests|a crawler triggers a state change through GET|use an appropriate mutating HTTP method and CSRF protection
servlet|response commitment|prevents changing headers after the response is sent|an error handler cannot set its status code|set status and headers before writing or flushing the body
servlet|multipart handling|parses uploaded form parts|large uploads consume excessive memory|set multipart limits and stream or spool parts safely
servlet|forward and redirect|either transfers control inside the server or asks the client to navigate|a redirect unexpectedly loses request attributes|use a forward for same-request state or persist state explicitly
rest|resource paths|map URI paths to resource methods|two methods conflict for the same request|make path and HTTP method matching unambiguous
rest|content negotiation|chooses a representation using media types|clients receive 406 or 415 on valid-looking requests|align Accept and Content-Type with produces and consumes declarations
rest|parameter conversion|binds path, query, and header values to Java types|malformed input reaches business logic unexpectedly|validate converted parameters and map client errors consistently
rest|exception mapping|turns application exceptions into HTTP responses|internal stack traces reach API clients|register an exception mapper that returns safe error bodies
rest|request filters|inspect or modify inbound REST requests|authorization applies to some endpoints but not others|bind the filter at the intended global or name scope
rest|response filters|modify outbound REST responses|correlation headers disappear on error responses|apply response filters across normal and mapped error paths
rest|REST client timeouts|bound remote call duration|a dependency outage exhausts request threads|set connect and read timeouts and use a bounded retry policy
rest|idempotent updates|allow safe retry of a defined operation|retries create duplicate resources|use stable resource identifiers or idempotency keys
rest|pagination|limits the result set returned per request|a list endpoint becomes slow as the table grows|use bounded pages and stable ordering or cursors
rest|conditional requests|use validators such as ETag for cache and concurrency|clients overwrite unseen changes|require a matching conditional update validator
cdi|type-safe injection|resolves a bean by type and qualifiers|deployment fails with an ambiguous dependency|add a qualifier or narrow the available beans
cdi|qualifiers|distinguish beans of the same type|the wrong implementation is selected|annotate the injection point and implementation with the same qualifier
cdi|bean scopes|define instance lifetime and contextual identity|request state appears in another user's session|choose the scope that matches the state lifetime
cdi|dependent scope|ties an instance to the injection target's lifecycle|a dependent object is retained longer than expected|review the owning bean lifecycle and destruction
cdi|producer methods|expose objects through CDI injection|a third-party object cannot be injected directly|provide a producer with appropriate scope and disposal
cdi|interceptors|apply cross-cutting behavior around invocations|an annotated method bypasses auditing through self-invocation|call through the managed proxy or move behavior to another bean
cdi|decorators|wrap business interfaces selectively|a decorator is never invoked|verify the decorated type and decorator enablement
cdi|events|decouple observers from event producers|an observer runs at an unexpected transaction phase|select the intended synchronous or transactional observer phase
cdi|alternatives|select a replacement bean for a deployment|a test implementation runs in production|limit alternative selection to the intended deployment
cdi|passivation|serializes beans held in passivating scopes|session restoration fails for a nonserializable dependency|make the bean passivation capable or use another scope
persistence|entity identity|maps an entity key to database identity|two rows collapse into one managed object|verify the primary key mapping and equality contract
persistence|persistence context|tracks managed entities and changes|edits to a detached entity are not saved|merge the detached state or reload a managed entity
persistence|flush|synchronizes pending changes with the database|a constraint error appears only at commit|flush at a controlled point when early validation is needed
persistence|lazy relationships|defer loading an association|rendering accesses a relation after the context closes|fetch needed data within the transaction or use a projection
persistence|eager relationships|load an association with its parent|one endpoint loads a large unwanted graph|prefer targeted fetch plans for that use case
persistence|N plus one queries|repeat a query per parent object|one page request issues hundreds of selects|use a join fetch, entity graph, or batch fetch after measuring
persistence|optimistic locking|detects conflicting updates with a version|concurrent edits silently overwrite each other|add a version field and handle conflict retries at the use-case boundary
persistence|pessimistic locking|locks database rows during a transaction|a hot row stalls unrelated requests|keep lock duration short and review contention
persistence|JPQL parameters|bind values separately from query syntax|user input changes query structure|use typed parameters rather than string concatenation
persistence|transaction-scoped entity managers|bind persistence state to one transaction|an entity manager is shared across threads|obtain a context per transaction and avoid sharing it across threads
transactions|atomic commit|commits all work or rolls it back|an order is saved while its payment record is missing|put both database changes in one transaction where possible
transactions|transaction propagation|determines how a called method joins a transaction|a nested call commits independently of its caller|choose the transaction attribute that matches the boundary
transactions|rollback rules|determine which failures mark a transaction for rollback|a checked business exception commits partial work|configure rollback behavior for that exception
transactions|transaction timeout|bounds a transaction's running time|locks remain held during a slow remote call|move remote work outside the database transaction and set a timeout
transactions|two-phase commit|coordinates multiple XA resources|a distributed transaction blocks during a coordinator outage|minimize XA participants and plan recovery of in-doubt branches
transactions|saga compensation|reverses completed steps across independent services|a multi-service workflow partly completes|record steps and implement idempotent compensating actions
transactions|outbox pattern|publishes an event reliably with a database change|the database commits but the event is lost|write an outbox record in the same transaction and publish asynchronously
transactions|read isolation|controls which concurrent changes a transaction sees|a read-modify-write flow sees inconsistent data|choose isolation or locking based on the invariant and measured contention
transactions|connection pool boundaries|return connections after transactional work|the pool empties under traffic|close acquired resources and shorten transactions
transactions|transactional tests|verify rollback and commit behavior|tests pass although rollback semantics are broken|assert persisted state after success and failure paths
security|declarative authorization|restricts methods or URLs by role|an endpoint is reachable without the required role|apply role constraints and test the effective security mapping
security|authentication mechanism|establishes a caller identity|an API accepts unauthenticated requests|configure a supported authentication mechanism and protect routes
security|principal propagation|passes caller identity into managed calls|background work runs without the expected identity|propagate security context through managed facilities
security|least privilege|limits access to only necessary operations|a service account can alter unrelated tables|narrow roles and database grants to required actions
security|CSRF protection|prevents unwanted browser-authenticated writes|a third-party page can submit an authenticated form|validate an anti-CSRF token for state-changing browser requests
security|output encoding|treats untrusted text as data in HTML|a stored comment executes script in a browser|encode output for its HTML context and avoid unsafe insertion
security|secret rotation|replaces credentials without exposing them in code|credential replacement requires a code rebuild|load secrets from managed configuration and rehearse rotation
security|transport security|protects data in transit|credentials cross the network in clear text|require TLS and enforce secure transport settings
security|session fixation defense|changes session identity after login|an attacker-chosen session survives authentication|rotate the session identifier on successful login
security|audit trails|record sensitive operations with actor context|an incident cannot be traced to a principal|log actor, action, outcome, and correlation ID without secrets
messaging|queues|deliver a message to one consumer in a competing group|each worker processes the same job unexpectedly|send work to a queue and check consumer configuration
messaging|topics|fan out messages to subscribers|an expected subscriber misses an event|verify subscription durability and activation timing
messaging|acknowledgment|marks successful message processing|messages are replayed after a crash|make handling idempotent and acknowledge only after durable work
messaging|dead-letter handling|isolates repeatedly failing messages|one poison message blocks progress|set redelivery limits and route failures to a dead-letter destination
messaging|message ordering|depends on destination and consumer topology|events for one aggregate arrive out of order|partition by aggregate key and handle sequence checks
messaging|at-least-once delivery|may redeliver a message after failure|a retry charges a customer twice|deduplicate by a stable message or business operation ID
messaging|message-driven beans|process messages under container management|a listener fails to receive messages after deployment|verify destination activation configuration and transaction settings
messaging|request-reply messaging|correlates asynchronous responses with requests|responses attach to the wrong pending request|use a unique correlation ID and expiry
messaging|message expiration|sets a lifetime for stale work|obsolete tasks execute hours later|set time-to-live and handle expiration explicitly
messaging|backpressure|limits producers when consumers lag|queue depth grows without bound|measure lag and cap or throttle production
validation|Bean Validation constraints|declare field and property invariants|invalid input is persisted|validate at the boundary and handle constraint violations
validation|validation groups|apply different constraints in different workflows|update-only rules reject a create request|select the correct group for each operation
validation|cascaded validation|checks nested objects marked for validation|invalid nested values pass the outer check|mark the association for cascaded validation
validation|custom constraints|encapsulate reusable domain checks|the same rule diverges across endpoints|implement one constraint validator with clear semantics
validation|cross-field validation|checks relationships between fields|each field passes but the combined request is invalid|use a class-level constraint or domain validation method
validation|method validation|checks parameters and return values|a service accepts invalid arguments outside HTTP|enable validation at the service boundary
validation|constraint message interpolation|renders user-facing validation messages|raw template keys appear in API errors|configure message bundles and safe API error mapping
validation|database constraints|protect invariants even outside the application|concurrent requests bypass an application-only uniqueness check|enforce uniqueness in the database and map conflicts
validation|validation boundaries|reject invalid input before expensive work|bad payloads reach downstream services|validate at ingress and recheck critical domain invariants
validation|validation error format|reports field failures consistently|clients cannot identify the rejected field|return a stable structured field-error response
concurrency|managed executors|run background work under container control|ad hoc threads lose application context|submit work through a managed executor
concurrency|context propagation|carries selected context into tasks|async work loses identity or naming context|configure the managed context propagated to the task
concurrency|bounded task queues|prevent runaway memory use|a traffic spike creates millions of pending tasks|bound queue capacity and define rejection behavior
concurrency|structured cancellation|stops work no longer needed|timed-out requests leave expensive tasks running|propagate cancellation and enforce task timeouts
concurrency|thread-safe bean state|protects data shared across requests|a singleton counter produces inconsistent values|use atomic operations or externalize mutable state
concurrency|scheduled tasks|run timed jobs using managed scheduling|the same job fires on every cluster node|coordinate cluster ownership or make the job idempotent
concurrency|connection pool sizing|balances concurrency against database capacity|more worker threads increase database wait time|size the pool from measured throughput and database limits
concurrency|bulkheads|isolate slow dependency workloads|one remote dependency consumes every worker|use separate bounded pools or semaphores per dependency
concurrency|timeouts and retries|bound latency while handling transient failures|retries amplify an outage|set budgets, jitter, and retry only safe operations
concurrency|graceful shutdown|lets in-flight work finish before termination|deployments interrupt active requests and messages|stop intake and drain work within a bounded deadline
""".strip().splitlines()

ROWS = [line.split("|") for line in FACTS]
assert len(ROWS) == 100, len(ROWS)
assert all(len(row) == 5 and row[0] in SOURCES for row in ROWS)


def question(row: list[str], index: int, tier: str) -> dict:
    category, concept, behavior, symptom, response = row
    field = 2 if tier == "basic" else 4
    prompt = (f"In Jakarta EE, what is the main purpose of {concept}?" if tier == "basic"
              else f"{symptom[0].upper() + symptom[1:]}. Which change addresses this failure?")
    # Competing answers stay within the subject area. No synthetic lead-ins or
    # answer permutations are counted as new questions.
    others = [r[field] for r in ROWS if r[0] == category and r[1] != concept]
    offset = index % len(others)
    wrong = [others[(offset + j * 3) % len(others)] for j in range(3)]
    return choice(
        f"ee-{tier}-{index + 1:03d}-01", prompt, row[field], wrong,
        f"{concept[0].upper() + concept[1:]} {behavior}. When {symptom}, {response}.",
        concept, SOURCES[category],
        assessment(f"ee-{slug(concept)}-{'purpose' if tier == 'basic' else 'repair'}",
                   "recall" if tier == "basic" else "debug", slug(concept)),
        "easy" if tier == "basic" else "medium",
    )


def courses() -> list[dict]:
    result = []
    for tier, difficulty in [("basic", "easy"), ("medium", "medium")]:
        tests = []
        for category in SOURCES:
            items = [question(row, i, tier) for i, row in enumerate(ROWS) if row[0] == category]
            tests.append({"id": f"ee-{tier}-{category}-test", "title": f"{category.title()} practice",
                          "description": f"{tier.title()} Jakarta EE {category} questions.",
                          "difficulty": difficulty, "questions": items})
        result.append({"schema_version": 1, "id": f"ee-{tier}",
                       "title": f"Java Enterprise and Jakarta EE — {tier.title()}",
                       "description": f"100 distinct {'concept checks' if tier == 'basic' else 'failure diagnoses'} across ten enterprise subject areas.",
                       "subject": "Java Enterprise / Jakarta EE", "difficulty": difficulty,
                       "lessons": [], "tests": tests})
    return [*result, advanced_course(SOURCES), *java_courses(), competency_course(), dummy_course()]


def write_json(path: Path, value: object) -> str:
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def generate(out: Path = OUT) -> None:
    generated = courses()
    report = audit(generated)
    if report["errors"]:
        raise ValueError("Question quality checks failed:\n" + "\n".join(report["errors"]))
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for course in generated:
        name = {"ee-basic": "basic", "ee-medium": "medium", "ee-advanced": "advanced"}.get(course["id"], course["id"])
        path = out / f"{name}.json"
        preserve_revisions(course, json.loads(path.read_text()) if path.exists() else None)
        digest = write_json(path, course)
        entries.append({key: course[key] for key in ("id", "title", "description", "subject", "difficulty")} |
                       {"path": path.name, "sha256": digest})
    write_json(out / "catalog.json", {"schema_version": 1, "content_revision": 3,
                                    "collection_id": "tutorialz-jakarta-ee", "courses": entries})
    write_json(out / "coverage.json", report)
    print(f"Generated {report['questions']} questions; {len(report['review'])} similarity pairs to review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    generate(parser.parse_args().out)
