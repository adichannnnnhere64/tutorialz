## Understand

### Start with business invariants and ownership

Architecture organizes responsibilities, data, and failure handling around business needs. Begin with the domain: what must remain true, who owns each decision, and which changes must become visible together? An inventory invariant might forbid selling more units than are available. A settlement invariant might require every posted transfer to have balanced ledger entries. These rules are more useful starting points than choosing a messaging product or drawing one service per database table.

An aggregate is a consistency boundary for related domain state and behavior. A bounded context defines where a model and its language have a particular meaning. Customer can mean a billing account in one context and a delivery recipient in another. Sharing one universal object across every team often creates accidental coupling. Translate at boundaries rather than assuming identical names imply identical semantics.

A modular monolith can enforce useful domain boundaries without introducing network calls between every module. Microservices add independent deployment and scaling opportunities but also introduce partial failure, distributed tracing, message evolution, and cross-service consistency problems. Choose the deployment boundary from ownership, change rate, scale, and operational capability. More services are not automatically more advanced architecture.

### Consistency must describe user-visible behavior

Strong local transactions can protect an aggregate or database invariant. Across independent services, a workflow may expose intermediate states and eventual consistency. Eventual does not mean “whenever something happens”: define expected convergence, maximum acceptable delay, reconciliation, and what the user sees while work remains pending.

Read-your-writes means a caller can observe its own completed update through the chosen read path. A lagging replica or asynchronous projection may not provide that immediately. A successful command response can include the authoritative result or a version token that lets the client reason about later reads. Do not label every stale read a database defect when the architecture deliberately introduced an asynchronous read model.

### Failure is part of the normal model

A timeout means the caller did not receive a timely outcome, not necessarily that the operation failed. A message can be redelivered after the consumer's business commit. A process can crash between two individually successful steps. Model these windows explicitly and assign an owner to recovery.

Durable state machines are useful for long-running work because progress survives one process. Each transition needs preconditions, an operation identity, an outcome, and a retry or compensation policy. An in-memory chain of callbacks may coordinate a short calculation, but it is not automatically a recoverable business workflow.

## Apply

### Example ARCH1: Order, payment, and shipment

A workflow creates an order in PENDING state, reserves inventory, authorizes payment, and requests shipment. Each participating service commits its own state. If payment is declined, inventory reservation is released and the order becomes rejected. If shipment fails after payment capture, the business may need a refund and manual review rather than pretending the payment never happened.

The worked design is a saga: coordinated local transactions with explicit compensation. Persist the workflow ID, step state, and external operation IDs. A compensation is a new business action and can itself fail. “Refund requested” and “refund completed” should be separate states when the provider processes asynchronously.

### Example ARCH2: Close the publish gap with an outbox

The order service stores the order and an outbox event in one local transaction. A relay publishes committed events to the broker. If the process crashes before commit, neither record exists. If it crashes after commit but before publish, the pending event remains available for recovery. If it crashes after publish but before recording success, the relay may publish again.

That last case is why the outbox requires duplicate-tolerant consumers. It guarantees durable publication intent alongside local state, not an exactly-once global business effect. Preserve a stable event ID across retries, and define ordering per aggregate if consumers depend on it. Monitor pending age, failed publications, and replay progress.

### Example ARCH3: Consume through a durable inbox boundary

A billing consumer receives event E17. In one local transaction it records E17 under the consumer's identity and updates its local billing state. A uniqueness constraint prevents the same consumer from applying E17 twice. Acknowledgement happens only after the required durable outcome.

If acknowledgement is lost, redelivery finds the existing inbox record and follows the duplicate policy. The deduplication record and business update must be atomic together; writing the record first in one transaction and the charge later in another can lose work. For an external payment provider, a local inbox alone cannot atomically include the remote charge: use provider idempotency and reconciliation as well.

### Example ARCH4: Put AI behind a business boundary

An AI assistant proposes a refund as structured JSON. The application validates the shape, retrieves the authoritative order, checks identity and refund policy, calculates the allowed amount, and obtains any required approval before executing a refund operation with a stable key.

The model's suggestion is untrusted input, not authorization. Retrieved documents can contain hostile instructions, and a syntactically valid amount can still be wrong. Keep tool permissions narrow, separate explanation from execution, and log safe decision evidence. A human-facing suggestion feature and an autonomous payment executor have materially different risk and approval requirements.

## Advanced

### Saga coordination and isolation

Orchestration gives a coordinator explicit responsibility for directing steps and recording workflow progress. Choreography lets services react to domain events without one central command sequence. Either can work, but ownership, observability, cycle prevention, and schema evolution become important as the workflow grows. A visually decentralized event graph can still be tightly coupled through hidden timing assumptions.

Sagas do not automatically provide ACID isolation across all steps. Concurrent workflows can observe intermediate state. Reservations, semantic locks, version checks, and domain rules can prevent conflicting actions where necessary. Choose which transitions are compensable and identify irreversible steps before execution. Some failures require forward recovery or human resolution rather than a mechanical inverse.

Compensation should be idempotent and operate on the original step's identity. Releasing reservation R42 is safer than blindly adding ten units to inventory whenever a retry occurs. Compensation order may depend on domain relationships, not merely reversing a list. Record attempted and completed compensation separately so recovery can distinguish uncertainty from confirmed failure.

### Event sourcing, CQRS, and projections

Event sourcing stores domain state changes as the authoritative history and derives current state from them. An outbox stores publication intent alongside another authoritative model; it is not automatically event sourcing. CQRS separates command and query models and can be used with or without event sourcing. Avoid treating these patterns as an inseparable package.

Projections need replay, schema evolution, ordering, and idempotence. Replaying historical events through current code can change results if semantics have changed. Version event contracts and transformation logic deliberately, and define how to repair or rebuild projections. Retaining an immutable event log also creates privacy and retention responsibilities; do not store unnecessary sensitive data simply because events are convenient.

### Resilience budgets and failure amplification

A timeout bounds waiting; a retry attempts work again; a circuit breaker temporarily rejects calls to a failing dependency; a bulkhead isolates capacity. These mechanisms solve different problems. None proves an operation is safe to repeat. Retrying a non-idempotent payment can produce duplicate effects even when the retry library behaves perfectly.

Allocate an end-to-end deadline and a retry budget. Include queue time, connection acquisition, and all nested calls. Backoff and jitter reduce synchronized retry waves, while bounded concurrency prevents one dependency from consuming every worker. A fallback must preserve honest business meaning: returning an estimated delivery date may be acceptable, inventing a successful payment is not.

Caches improve read latency but add invalidation, freshness, and tenant-isolation concerns. Cache stampedes can overload the source when a popular entry expires. Use appropriate request coalescing, expiry variation, and bounded refresh policies. Do not let stale authorization or balance data silently become the authority for a high-impact decision.

### Distributed coordination and fencing

A distributed lease can expire while an old owner is paused and later resumes. Simply acquiring a lock once does not guarantee the stale owner stops writing. Fencing tokens let the protected resource reject operations from older owners when implemented correctly. The resource must enforce the token; a counter stored only in the worker's memory provides no protection.

For scheduled jobs, define ownership, lease renewal, retry, overlap policy, and checkpointing. A cluster singleton annotation or one scheduled method per JVM does not establish global uniqueness. Often an idempotent job with durable partition ownership is easier to recover than a fragile attempt to guarantee that code executes only once under every failure.

## Production

### Observe operations across boundaries

Observability should connect a user's operation to HTTP calls, database changes, outbox records, broker messages, and consumer outcomes. Propagate correlation and trace context through supported mechanisms while keeping business operation IDs stable across retries. A trace ID describes an execution path; it is not always the durable deduplication key for a business action.

Metrics should track business progress as well as infrastructure: pending order age, compensation failures, outbox lag, duplicate rate, and reconciliation backlog. Use bounded dimensions and protect sensitive data. A broker being reachable does not prove orders are completing. Define service-level objectives around meaningful user outcomes and alert on actionable deviations.

### Evolve contracts and deploy safely

Use backward-compatible message and API changes during rolling deployments. Old consumers may still process queued messages long after a new producer is deployed. Keep schema versioning and default behavior explicit; adding an enum value can break a consumer that assumes a closed set. Test replay and mixed-version operation with realistic retained data.

Record architecture decisions with context, considered alternatives, consequences, and revisit criteria. A decision to use local transactions plus outbox should state why XA was not selected and which consistency tradeoffs users accept. A decision to remain a modular monolith should describe boundaries and ownership, not be treated as unfinished microservices work.

### Evaluate newer technology through constraints

Virtual threads, native images, reactive stacks, and AI integration each change different parts of the system. Virtual threads can improve blocking concurrency but not database capacity. Native compilation can improve startup or footprint but requires build-time knowledge of reflection, proxies, resources, and dynamic loading. Reactive execution needs an end-to-end strategy for blocking boundaries and demand.

AI systems add nondeterministic outputs, prompt-injection risks, evaluation needs, and data-governance questions. Validate outputs against trusted state, restrict tools, and measure task-specific failure modes before granting consequential authority. A model's fluent explanation is not evidence that a proposed action satisfies domain invariants. Keep human approval for the actions whose risk or organizational policy requires it.

## Exam reasoning

### Find the invariant before choosing the pattern

If a question asks how to keep an order and its publication intent together, consider the local transaction/outbox boundary. If it asks how to coordinate independently committed services, consider a saga and compensation. If it asks how a consumer tolerates redelivery, identify the inbox or other durable idempotency boundary. Naming a broker alone does not answer these different problems.

Trace crash points and ask what durable evidence remains after each. A design that works only when every step returns normally is incomplete. For consistency questions, identify which read model is being queried and whether read-your-writes is promised. For resilience, distinguish safe retries from failure amplification and honest fallback from fabricated success.

Avoid “always” answers such as every application needs microservices, every event system is event-sourced, or every distributed lock prevents duplicate effects. The right choice depends on ownership, latency, integrity, deployment independence, and recovery. Good architecture explains both the guarantee and the burden introduced.

## Cheatsheet

| Requirement | Design question |
| --- | --- |
| Domain invariant | What must remain true and who enforces it? |
| Aggregate | Which state changes need one consistency boundary? |
| Bounded context | Where does this model and vocabulary apply? |
| Saga | Which local steps and compensations are recoverable? |
| Outbox | Is business state atomic with publication intent? |
| Inbox | Is deduplication atomic with the consumer's local effect? |
| External effect | Does the provider support idempotency and reconciliation? |
| CQRS | Separate command/query models, not necessarily event sourcing |
| Event sourcing | Authoritative history with replay and evolution obligations |
| Resilience | Deadlines, bounded retries, bulkheads, honest fallbacks |
| Lease ownership | Can the resource fence out a stale owner? |
| Observability | Can one operation be followed to durable completion? |
| Native/AOT | Are dynamic resource and reflection requirements known? |
| AI integration | Untrusted output behind authorization and business rules |

## Check yourself

### 1. Service boundary

Is one service per database table a sufficient domain design?

**Answer:** No. Boundaries should reflect invariants, ownership, language, and change. Table structure alone does not describe business responsibility.

### 2. Compensation

Is a refund the same as rolling back an old database transaction?

**Answer:** No. It is a new business operation with its own failure, timing, and audit semantics. The original payment may remain historically real.

### 3. Outbox identity

Should a relay generate a new event ID every time it retries the same outbox row?

**Answer:** No. Preserve a stable event identity so consumers can recognize repeated delivery according to their deduplication contract.

### 4. Advanced: inbox gap

Why must the inbox record and local business effect commit together?

**Answer:** Separate commits can either mark unperformed work as complete or perform work without recording deduplication. One atomic boundary avoids those local crash windows.

### 5. Advanced: stale lock owner

Why might a distributed lease need a fencing token?

**Answer:** An old owner can resume after its lease expires. The protected resource must reject stale-owner operations; lease acquisition alone cannot force that process to stop.

### 6. Advanced: AI authorization

An AI response passes JSON schema validation. Can it directly authorize a refund?

**Answer:** No. Shape validation does not establish identity, ownership, eligibility, amount, or approval. Enforce trusted business and authorization rules before any consequential action.

## Sources

Reviewed 2026-09-26. Concepts are implementation-independent unless a technology/version is named. Scenarios are original engineering exercises, not proprietary assessment content.

- [Saga pattern and tradeoffs](https://microservices.io/patterns/data/saga.html)
- [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [Idempotent consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
- [CQRS](https://microservices.io/patterns/data/cqrs.html)
- [Event sourcing](https://microservices.io/patterns/data/event-sourcing.html)
- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/)
- [OWASP prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [GraalVM reachability metadata](https://www.graalvm.org/latest/reference-manual/native-image/metadata/)
