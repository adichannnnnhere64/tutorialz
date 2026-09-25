## Understand

### Enterprise Beans are managed business components

Jakarta Enterprise Beans, still commonly called EJB, provide container-managed transactions, security, concurrency, lifecycle, asynchronous invocation, timers, and messaging integration. The component model is not synonymous with persistence entities: modern database entities belong to Jakarta Persistence. This chapter targets Enterprise Beans 4.0 with Jakarta imports and distinguishes full functionality from the smaller Lite subset.

A stateless session bean has no conversational state assigned to a particular client between calls. Instances may be pooled and reused. Fields can hold injected collaborators or carefully managed instance state, but cannot reliably hold the current user's unfinished checkout across calls. Stateless does not mean the implementation has literally no fields, nor that its business operation cannot update a database.

A stateful session bean represents a client conversation and can retain conversational state between invocations. It needs a defined completion/removal policy and state suitable for passivation where applicable. A singleton session bean has one instance per application within the relevant container/JVM scope, with explicit concurrency rules. It is not a guaranteed cluster-wide singleton or distributed lock.

### Call through the managed view

Clients use a local, remote, or no-interface business view as appropriate. A direct new operation creates an ordinary object without EJB services. A direct internal method call should not be assumed to re-enter container transaction, security, or asynchronous interception. Put boundaries in separate managed operations or use a supported business reference where necessary.

Local and remote views have different deployment and argument semantics. Remote calls add transport, serialization, latency, and uncertain-outcome failure modes. They are not ordinary local calls made magically reliable by an annotation. Design coarse-grained contracts and explicit value types, and avoid exposing live persistence objects as remote conversational state.

### CMT and BMT identify transaction ownership

Container-managed transactions, or CMT, use transaction attributes to define how an invocation joins, starts, suspends, or rejects a transaction. REQUIRED is the usual default: join an incoming transaction or start one if absent. REQUIRES_NEW uses a separate transaction and suspends the caller's one. MANDATORY requires an incoming transaction; NEVER rejects one; SUPPORTS uses one if present; NOT_SUPPORTED executes without the caller's transaction.

Bean-managed transactions, or BMT, let eligible beans explicitly use UserTransaction. BMT is not permission to mix arbitrary connection commits with a global transaction. Lifecycle restrictions vary by bean kind; stateful beans have special conversational rules. Choose one ownership model deliberately and understand how resources enlist. CMT code should not call UserTransaction to override the container's boundary.

## Apply

### Example B1: Declare a business transaction

Enterprise Beans 4.0 fragment; Inventory is an injected business collaborator.

```java
@jakarta.ejb.Stateless
public class Reservations {
  @jakarta.ejb.EJB
  Inventory inventory;

  @jakarta.ejb.TransactionAttribute(jakarta.ejb.TransactionAttributeType.REQUIRED)
  public void reserve(long productId, int quantity) {
    inventory.reserve(productId, quantity);
  }
}
```

The invocation joins an incoming transaction or starts a new one when called through its managed view. The annotation does not validate quantity or define inventory concurrency. The collaborator must enforce its business rules and use appropriately enlisted resources. If called with new Reservations, injection and transaction services do not appear automatically.

### Example B2: Make rollback intent explicit

Application exception declaration:

```java
@jakarta.ejb.ApplicationException(rollback = true)
class StockUnavailable extends Exception {
  StockUnavailable(String message) { super(message); }
}
```

A checked business exception does not automatically imply rollback under the application-exception rules. This declaration explicitly requests it. An application exception is something the client can meaningfully handle, such as insufficient stock; an unexpected infrastructure failure is a different category. Decide rollback behavior based on integrity, not on whether the exception's name sounds severe.

### Example B3: Guard singleton state

Enterprise Beans fragment using container-managed concurrency.

```java
@jakarta.ejb.Singleton
@jakarta.ejb.Lock(jakarta.ejb.LockType.READ)
public class CatalogVersion {
  private long version;
  public long current() { return version; }

  @jakarta.ejb.Lock(jakarta.ejb.LockType.WRITE)
  public void advance() { version++; }
}
```

Read locks permit concurrent reader invocations, while the write operation obtains exclusive access under the container's concurrency rules. The default for container-managed singleton concurrency is WRITE when not overridden. This protects the singleton instance, not every copy deployed across a cluster. A durable global catalog version belongs in shared authoritative storage with its own concurrency contract.

### Example B4: Return an asynchronous result

Enterprise Beans fragment; report generation is illustrative.

```java
@jakarta.ejb.Stateless
public class Reports {
  @jakarta.ejb.Asynchronous
  public java.util.concurrent.Future<String> generate(long orderId) {
    return new jakarta.ejb.AsyncResult<>("report:" + orderId);
  }
}
```

The caller receives a container-managed Future before execution completes. The AsyncResult returned by the method communicates the result to the container; it is not the same object originally returned to the caller. Execution failures can be observed through the caller's Future. A void asynchronous method has no such result channel and needs deliberate operational error reporting.

## Advanced

### Transaction propagation across boundaries

A synchronous REQUIRED chain can share one transaction. If an inner operation marks it rollback-only, catching the exception does not make it committable again. The outer owner eventually encounters rollback rather than successful commit. REQUIRES_NEW isolates the inner transaction's outcome, but its commit can survive a later outer rollback, so use it only when that business meaning is intended.

Asynchronous EJB invocation does not propagate the caller's transaction. REQUIRED on the async operation therefore starts its own transaction rather than joining the caller. Caller security principal propagation follows the component's specified security behavior, which is distinct from transaction propagation. Do not assume every context either propagates together or disappears together.

A separate inner transaction can require additional resource capacity while the outer one still holds connections or locks. This can cause pool exhaustion or lock waits. A design using REQUIRES_NEW for every row in a large loop may have very different atomicity and performance from one batch transaction. Analyze resource ownership and failure meaning before selecting an attribute.

### Stateful lifecycle and passivation

Stateful beans support conversation state but should not become unbounded session caches. Define removal when the conversation completes, handle timeout, and keep state compact. Passivation moves suitable state out of active memory; activation restores it. Use lifecycle callbacks for resources that require reestablishment, within the specification's restrictions.

An extended persistence context can be associated with a stateful conversation in supported usage, but it is not a database transaction kept open for the entire user interaction. Detached-looking screens and stale state still need optimistic concurrency and authorization checks when a later operation commits. A user's long pause does not justify holding a database lock indefinitely.

Concurrent access to a stateful bean has specified restrictions and timeout behavior; do not casually share one conversational reference among unrelated requests or users. The fact that a bean remembers values does not make it suitable as a global cache. Store durable workflow state explicitly if it must survive failures beyond the container's supported stateful-bean guarantees.

### Timers and message-driven beans

The timer service schedules container callbacks, with persistent and nonpersistent timer choices. A timer callback is not proof of exactly-once business execution across every crash scenario. Make scheduled work idempotent, record progress, and understand the server's clustered timer implementation. A singleton plus a schedule annotation does not by itself establish one execution across all nodes.

A message-driven bean, or MDB, consumes messages through a resource adapter and container configuration. It has no ordinary client business view for invoking message processing directly. Multiple instances can process concurrently, so message ordering and state ownership need deliberate design. The listener transaction and acknowledgement behavior depend on the configured transaction model and resource integration.

For transactional message consumption, successful business commit and message consumption can be coordinated when the participating resources and manager support the required arrangement. Do not assume a non-XA database and broker become one atomic resource automatically. Redelivery remains relevant, especially around failures; use stable message IDs or operation keys and idempotent effects.

### Exception categories and recovery

Application exceptions report expected business outcomes. Their rollback behavior can be declared, and inheritance metadata affects how subclasses are classified. System exceptions represent failures the bean cannot handle as ordinary business outcomes; the container applies specified rollback and instance-handling behavior. Do not convert every system failure into a success-shaped response merely to avoid an exception.

For asynchronous calls, distinguish a failure to dispatch from a failure during execution. A client-side timeout or lost remote response may leave the actual business outcome uncertain. Retrying a remote operation requires a stable operation identity or another safe reconciliation strategy. A Future cancellation request does not guarantee that an already dispatched operation stops or rolls back its effects.

## Production

### Configure the runtime, not only annotations

Verify datasource and messaging bindings, transaction recovery storage, security-role mappings, instance pools, concurrency limits, and timer persistence. An application can compile against the Enterprise Beans API while the chosen servlet-only container does not implement EJB services. Profile support and server configuration are part of the deployment contract.

Monitor invocation latency, pool wait, transaction rollback rates, timer delays, MDB backlog, and redelivery. Distinguish resource starvation from slow business logic. A hundred MDB instances against ten database connections may increase waiting and contention rather than throughput. Bound processing concurrency according to the scarce dependency and broker behavior.

### Test container behavior directly

Plain unit tests are useful for domain logic but do not verify transaction attributes, lock annotations, passivation, timer recovery, or security interception. Add container-backed tests for those boundaries. Exercise a rollback-only inner call, async invocation without caller transaction propagation, concurrent singleton access, and message redelivery after failure.

During deployment, coordinate old and new consumers with schema evolution and message compatibility. A rolling upgrade may run two application versions at once. Keep operations idempotent and maintain stable resource identities required for recovery. Replacing a transaction log or timer store without understanding pending work can turn a routine release into a recovery incident.

## Exam reasoning

### Identify bean kind and invocation path

Start with stateless, stateful, singleton, or message-driven. Then identify CMT or BMT, the client view, and whether the call passes through the container. These facts determine the available services. A transaction annotation on a directly constructed object does not establish a managed transaction.

For propagation questions, track the caller transaction and the target attribute. Treat asynchronous invocation separately because the caller's transaction does not flow into it. For singleton questions, distinguish container locking from cluster coordination. For exception questions, identify application versus system classification and explicit rollback metadata.

Avoid answers equating a timer with guaranteed exactly-once execution, a stateful bean with a permanently open database transaction, or stateless with no mutable fields whatsoever. Explain the lifetime and guarantee actually provided, then consider the application's resource and recovery requirements.

## Cheatsheet

| Feature | Guarantee and boundary |
| --- | --- |
| Stateless | No client conversation assigned between calls |
| Stateful | Client conversation with removal/passivation rules |
| Singleton | Shared instance per relevant container scope, not cluster lock |
| CMT | Container owns transaction demarcation |
| BMT | Bean uses supported explicit transaction control |
| REQUIRED | Join incoming or create transaction |
| REQUIRES_NEW | Separate outcome; caller transaction suspended |
| MANDATORY / NEVER | Require incoming transaction / reject it |
| SUPPORTS / NOT_SUPPORTED | Use if present / execute without caller transaction |
| ApplicationException | Explicit business category; rollback setting matters |
| Asynchronous | Caller transaction does not propagate |
| Timer | Scheduled callback; make effects recoverable and idempotent |
| MDB | Container messaging endpoint, often concurrent |
| READ / WRITE lock | Singleton concurrency, not distributed coordination |

## Check yourself

### 1. Stateless field

Can a stateless bean reliably keep one customer's cart between calls?

**Answer:** No. Pooled instances are not assigned to that client's conversation. Use an appropriate conversational or durable state model.

### 2. Required without caller

What does REQUIRED do when no transaction arrives?

**Answer:** The container starts a transaction for the invocation, assuming a valid managed CMT call.

### 3. Checked business failure

Does every checked application exception automatically roll back CMT work?

**Answer:** No. Rollback metadata or explicit rollback-only handling matters. Design the exception contract to preserve data integrity.

### 4. Advanced: async propagation

Does an asynchronous REQUIRED method join the caller's transaction?

**Answer:** No. The caller's transaction does not propagate across the asynchronous invocation, so the target has its own transaction semantics.

### 5. Advanced: cluster singleton

Do singleton WRITE locks coordinate the same application across three JVMs?

**Answer:** Not by the portable singleton contract alone. They protect the relevant instance. Use an explicit distributed coordination or shared-storage strategy for a global invariant.

### 6. Advanced: caught rollback

An inner REQUIRED call marks the shared transaction rollback-only. Can catching its exception restore commit?

**Answer:** No. Catching changes Java control flow, not the transaction's rollback-only state. The outer owner must handle the failed transaction outcome.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta Enterprise Beans 4.0. Fragments require a supporting container and application dependencies.

- [Enterprise Beans 4.0 core specification](https://jakarta.ee/specifications/enterprise-beans/4.0/jakarta-enterprise-beans-spec-core-4.0)
- [Enterprise Beans API](https://jakarta.ee/specifications/enterprise-beans/4.0/apidocs/)
- [Enterprise Beans overview tutorial](https://jakarta.ee/learn/docs/jakartaee-tutorial/current/entbeans/ejb-intro/ejb-intro.html)
- [Jakarta Transactions 2.0](https://jakarta.ee/specifications/transactions/2.0/)
- [Jakarta Messaging 3.1](https://jakarta.ee/specifications/messaging/3.1/)
- [Jakarta EE 10 platform](https://jakarta.ee/specifications/platform/10/)
