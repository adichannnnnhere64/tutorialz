## Understand

Begin architecture with business invariants and failure cases. An order workflow might reserve stock, authorize payment and arrange shipping. Decide which changes must be atomic, which can be eventually consistent, and what users should see while work is incomplete. A service boundary should reflect ownership and change, not merely a database table.

A saga coordinates independently committed steps and compensations. Compensation is a new business operation, not a database rollback across arbitrary systems; it may fail and need retry or manual resolution. Persist workflow state and operation IDs so recovery does not depend on one process's memory.

Resilience needs budgets. Bound timeouts, retries, queue capacity and concurrent work. A circuit breaker stops calls during repeated failure, then permits limited recovery probes. A bulkhead isolates capacity so one dependency cannot consume every worker. Retries need backoff, jitter and idempotency to avoid amplifying an outage.

## Apply

An order service saves an order and outbox event in one local transaction. A relay publishes the event to the broker. Billing records the event's operation ID and resulting charge atomically in its own store. If acknowledgment is lost, the event can be retried without charging twice. Shipping may require a separate step and compensation if fulfillment becomes impossible.

Write the recovery cases before choosing a framework: crash before commit, after commit but before publish, after publish but before acknowledgment, and during compensation. Each case needs an owner and a recoverable state transition.

## Cheatsheet

| Requirement | Design question |
| --- | --- |
| Exactly-once business effect | Where is the durable deduplication boundary? |
| Read-your-writes | Which read path sees the committed state and when? |
| Multi-tenant cache | Does every key and permission check include the tenant boundary? |
| Cluster scheduled job | Who owns execution, and how is a failed owner replaced? |
| AI integration | Treat generated output as untrusted; validate schema and authorize actions separately |
| AOT/native deployment | Which reflection, resource and proxy needs must be known at build time? |
| Domain knowledge | What invariant matters to users: balance, inventory, eligibility or settlement? |
| Observability | Can an operation be traced across synchronous and asynchronous boundaries? |

## Check yourself

An AI response passes JSON schema validation. Can it directly authorize a refund?

**Answer:** No. Schema validation establishes shape, not identity, eligibility, ownership or financial authority. Enforce the refund's business and authorization rules using trusted application state before taking action.

## Sources

[Saga pattern](https://microservices.io/patterns/data/saga.html) · [Outbox pattern](https://microservices.io/patterns/data/transactional-outbox.html) · [Circuit breaker](https://microservices.io/patterns/reliability/circuit-breaker.html) · [OWASP GenAI guidance](https://genai.owasp.org/)
