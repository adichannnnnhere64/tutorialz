## Understand

### Baseline and learning objectives

This chapter uses Spring Framework 6.2 on Java 17, with Spring Boot 3.5 where auto-configuration is involved. Later Framework 7 and Boot 4 behavior must be checked separately. Know Java interfaces, exceptions, object lifetime and basic database transactions first. Your goals are to explain how a bean becomes usable, where interception occurs, and which component owns each resource or transaction.

Spring is a container and programming model, not a substitute for Java semantics. An annotation records metadata. Appropriate infrastructure must discover that metadata and apply behavior to a managed object. Calling a constructor directly can produce a perfectly valid Java object without producing a transactional, cached or asynchronous Spring bean.

### Dependency injection and bean selection

Constructor injection makes required collaborators visible and supports tests that supply controlled implementations. A single constructor usually does not require an explicit `@Autowired`. Multiple candidates require a deliberate resolution rule: qualifiers narrow the candidate set, while a primary candidate supplies a preferred choice where applicable. Bean names and injection-point naming can participate in resolution, but relying on accidental names makes refactoring risky.

A stereotype such as `@Service` does not guarantee discovery. Check component-scan boundaries, configuration imports, active profiles and conditions. If creation fails, identify whether the definition is missing, multiple definitions qualify, or a chosen definition fails while being instantiated. These failures need different fixes.

### Scope, lifecycle and ownership

Singleton scope is per container and bean definition, not one object throughout every process or cluster. A singleton containing mutable request data can race between callers. Prototype scope creates instances on lookup, but injecting a prototype once into a singleton does not repeat that lookup for each later method call.

The lifecycle includes construction, dependency population, initialization callbacks, and applicable post-processing. Distinguish an object's own initialization from application readiness: dependent infrastructure, background consumers and database migration may impose additional ordering. Close resources you own, not resources whose lifetime belongs to the container. Prototype destruction requires particular care because the container does not manage the full destruction lifecycle of handed-out prototype instances.

## Apply

### Example S1: injecting a bean through a factory-method parameter

Framework 6.2 configuration fragment; requires `spring-context`. Application-defined Repository and Service types are intentionally omitted:

```java
@Configuration(proxyBeanMethods = false)
class Services {
    @Bean Repository repository() { return new Repository(); }
    @Bean Service service(Repository repository) {
        return new Service(repository);
    }
}
```

The parameter receives the managed repository. Contrast this with calling `repository()` directly inside `service()` when proxy bean methods are disabled: that is an ordinary Java call and constructs another object in this example. Prefer parameter injection to make dependencies explicit without depending on configuration-method interception. The expected relationship is that the service uses the repository resolved by the container.

### Example S2: obtaining a fresh prototype per operation

Framework 6.2 fragment; Job and its processing operation are application-defined. Imports are from Spring context, beans and stereotype packages:

```java
@Component
@Scope("prototype")
class Job {}

@Service
class Dispatcher {
    private final ObjectProvider<Job> jobs;
    Dispatcher(ObjectProvider<Job> jobs) { this.jobs = jobs; }
    Job next() { return jobs.getObject(); }
}
```

Each call to `next()` performs a container lookup. Assuming the displayed prototype definition is selected, repeated calls obtain different Job instances. If Dispatcher instead accepted a Job in its constructor and returned that field, every call would return the one injected instance. This is a lifetime distinction, not a guarantee that either Job or Dispatcher is thread-safe.

### Example S3: transaction boundary and checked-exception rollback

Framework 6.2 method fragment; transaction management must be enabled and an external caller must invoke the managed service through its proxy:

```java
@Transactional(transactionManager = "ordersTx",
               rollbackFor = IOException.class)
public void importOrders() throws IOException {
    loadAndPersistOrders();
}
```

The named manager must control the data source used by the persistence operation. The method body is an application placeholder. An IOException escaping through the interceptor matches the explicit rollback rule. Catching and suppressing that exception before the interceptor sees it changes the reasoning. A later database error may also appear only when work is flushed or committed, outside the apparent body of the method.

### Example S4: isolate tenants in a cache key

Framework 6.2 method fragment; caching must be enabled and the call must cross the relevant proxy:

```java
@Cacheable(cacheNames = "invoices", key = "{#p0, #p1}")
public Invoice findInvoice(String tenantId, long invoiceId) {
    return repository.findAuthorized(tenantId, invoiceId);
}
```

The indexed arguments avoid relying on retained parameter names. The composite key includes both values affecting identity. The repository and Invoice are application types. Cache separation does not replace authorization: design where access checks occur even on a cache hit, and determine whether permissions can change independently of cached data. A caller reaching a cached value must not bypass the required security boundary.

## Advanced

### Bean definitions versus bean instances

A BeanFactoryPostProcessor operates on configuration metadata. A BeanPostProcessor operates around instance initialization and may return a wrapped instance. These extension points are not interchangeable. Fetching arbitrary application beans too early during infrastructure setup can cause premature instantiation and prevent normal processing.

When declaring infrastructure post-processors through configuration, expose the relevant return type and use the documented static-factory arrangement where appropriate. Diagnose a bean reported as ineligible for full processing by tracing what caused its early creation, not by repeatedly adding stereotypes to it.

### Proxy boundaries and self-invocation

A JDK proxy exposes interfaces; a class-based proxy subclasses the target type and therefore faces Java inheritance constraints. Final classes cannot be subclassed, and final methods cannot be overridden for class-based advice. Method visibility and proxy type matter, so state the interception arrangement when answering an exam question.

In ordinary proxy mode, `this.save()` executes on the target rather than re-entering the proxy. It therefore does not apply a new transaction, cache or asynchronous interceptor for that internal call. Existing transaction context may still be present from the outer call: “the inner annotation is not intercepted” is different from “there is no transaction at all.” Moving the independently advised operation to another managed collaborator often makes the boundary clearer.

### REQUIRED, REQUIRES_NEW and NESTED

REQUIRED typically joins an existing transaction or starts one when necessary. Several logical scopes can share one physical transaction. If an inner participant marks the shared transaction rollback-only, an outer caller cannot make it committable merely by catching an exception; completion can report UnexpectedRollbackException.

REQUIRES_NEW uses an independent transaction and can retain outer resources while acquiring additional ones. That independence can be useful for a deliberate boundary, but it can exhaust a connection pool under concurrency. NESTED usually relies on savepoints with a suitable JDBC transaction manager; it is not a portable synonym for a second physical transaction or a universal feature of every JPA/JTA manager.

### Rollback rules, synchronization and commit timing

Default declarative rollback rules traditionally roll back for RuntimeException and Error, not every checked Exception. Explicit rules and Framework 6.2 configuration can change the defaults, so examine the actual configuration. A read-only flag is a transaction hint with manager/provider-specific consequences, not a universal prohibition that makes writes impossible.

A transaction-scoped callback can align actions with completion, but a callback is not a durable delivery mechanism. If a process crashes after commit and before publishing an event, an in-memory after-commit listener can lose the notification. Use a transactional outbox when the business requirement requires recovery across that failure window.

### Caching consistency and asynchronous context

A cache annotation does not turn a local provider into a coherent distributed cache. Define invalidation, TTL, ownership, key shape and failure behavior. `sync=true` requests coordinated loading through the provider's supported mechanism; it does not promise cluster-wide locking across arbitrary cache products.

Imperative transactions usually bind resources to the executing thread. Starting work on another executor does not automatically transfer those resources. Reactive transactions use reactive context and a supported reactive manager; unrelated subscriptions or thread-local assumptions can break the intended boundary. Know whether a method returns a publisher representing the work or starts work separately and returns too early.

## Production

### Diagnose connection-pool exhaustion

Suppose many requests each hold an outer transaction and call a REQUIRES_NEW audit operation. Each nested operation may need an additional connection while the outer one remains held. Inspect active connections, wait time, transaction duration and the call graph. Increasing the pool without understanding the concurrency pattern can merely move the failure to the database.

Consider whether the audit must be independently committed, can share the transaction, or belongs in an outbox. Make that decision from business durability requirements. Do not remove transaction boundaries merely to make a load test green; preserve the invariant and then bound concurrent work.

### Test the real transaction boundary

A test method that itself runs in a rolled-back transaction can hide behavior that only occurs at service commit. Test the service through its actual proxy and include a test that reaches genuine completion. Assert both the observable database state and the exception seen by the caller. Flush-time, commit-time and method-body failures are not always observed at the same line.

Use a real database integration test for isolation, locking and vendor constraints when those details matter. An in-memory substitute can be useful for fast feedback but does not establish another database's execution plans or concurrency semantics.

### Observe caches and background work

Measure cache hit rate together with correctness indicators: stale reads, tenant boundaries, eviction behavior and unexpected loader calls. Never log sensitive cached contents merely to confirm a key. For asynchronous work, define queue bounds, rejection behavior, error reporting and shutdown. A successful submission is not proof that the task completed or committed its work.

AOT/native-image builds require a separate compatibility check for reflection, resources and dynamic proxies. Supply necessary runtime hints and test the actual artifact. Passing a JVM test does not demonstrate that arbitrary runtime discovery will work in a closed-world native build.

## Exam reasoning

### Trace a call through the container

First identify the actual object reference: managed proxy, managed target, or manually constructed object. Next identify the method call path and whether it crosses the interceptor. Then determine transaction manager, propagation, existing context and exception outcome. This sequence is more reliable than counting annotations.

### Distinguish default behavior from configured behavior

“Singleton” answers a container scope question, not a thread-safety question. “Prototype” answers a lookup question, not whether a singleton repeatedly retrieves it. “Transactional” requires both infrastructure and interception. “Read-only” needs a manager/provider context. If a question specifies custom rollback rules, do not substitute the default rule from memory.

### Use versioned claims

Framework and Boot are different projects with different responsibilities. Boot supplies conventions and auto-configuration around Framework capabilities. The examples here intentionally use the 6.2/3.5 baseline. Do not silently apply a later version's defaults, dependency requirements or migration behavior to a question explicitly targeting this baseline.

## Cheatsheet

| Concept | Decision or diagnostic |
| --- | --- |
| Constructor injection | Make mandatory dependencies explicit |
| Qualifier / Primary | Narrow candidates / prefer an eligible candidate |
| Bean lifecycle | Construction, injection, initialization, processing and owned cleanup |
| BeanFactoryPostProcessor | Change bean-definition metadata |
| BeanPostProcessor | Process instances; may wrap them |
| Singleton scope | One scoped instance, not automatic thread safety |
| Prototype lookup | Use ObjectProvider when each operation needs a lookup |
| Proxy boundary | External intercepted call differs from self-invocation |
| REQUIRED | Participants can share physical transaction and rollback-only state |
| REQUIRES_NEW | Independent transaction; additional resource demand |
| NESTED | Savepoint-style semantics only with supported arrangements |
| Rollback rules | Check exception type and configured overrides |
| Read-only hint | Provider/manager behavior, not universal write enforcement |
| After-commit callback | Not a durable queue across process failure |
| Cache consistency | Tenant-aware keys, authorization, invalidation and provider semantics |
| Async context | Submission does not propagate every thread-bound resource |
| Reactive transaction | Work must participate in the appropriate publisher/context |
| AOT | Register dynamic needs and test the built artifact |

## Check yourself

### 1. Prototype captured once

A singleton stores one injected prototype and reuses it for every request. Is Spring recreating the prototype on each call?

**Answer:** No. Injection resolved one instance when the singleton was created. Use an explicit provider lookup when per-operation retrieval is required, then handle the returned object's ownership.

### 2. Configuration method call

With proxyBeanMethods disabled, a bean method directly calls another bean method that creates an object. Must the result be the managed singleton?

**Answer:** No. The direct invocation follows ordinary Java semantics. Inject the managed dependency through a method parameter when that relationship is intended.

### 3. Advanced: caught inner failure

An intercepted REQUIRED collaborator marks a shared transaction rollback-only. Its caller catches the exception and returns normally. Is successful commit guaranteed?

**Answer:** No. Catching an exception does not clear rollback-only state. The outer completion can fail with UnexpectedRollbackException rather than misleading the caller into believing a commit occurred.

### 4. Advanced: self-invoked REQUIRES_NEW

An outer transactional method calls this.audit(), which declares REQUIRES_NEW. Does ordinary proxy-based interception necessarily start the independent transaction?

**Answer:** No. Self-invocation does not cross the proxy. The existing outer transaction may remain active, but the inner annotation is not independently applied through that call.

### 5. Advanced: tenant-aware but unauthorized cache hit

The key includes tenant and invoice IDs. Can the cache now replace authorization?

**Answer:** No. Identity separation prevents key collisions but does not prove the caller's permission. Ensure access checks still apply when the method body is skipped on a hit, and account for permission changes.

### 6. Commit succeeds, event disappears

A process commits an order and crashes before its after-commit listener publishes an event. Which additional mechanism addresses recoverable delivery?

**Answer:** Persist an outbox record atomically with the order and relay it with retries and idempotent handling. An in-memory listener alone cannot recover an event that was never durably recorded.

## Sources

Reviewed 2026-09-25. Baseline: Java 17, Spring Framework 6.2 and Boot 3.5. Code blocks are framework fragments with the stated application collaborators, not standalone programs.

- [Framework 6.2 container extension points](https://docs.spring.io/spring-framework/reference/6.2/core/beans/factory-extension.html).
- [Framework 6.2 proxy mechanisms](https://docs.spring.io/spring-framework/reference/6.2/core/aop/proxying.html).
- [Framework 6.2 bean scopes](https://docs.spring.io/spring-framework/reference/6.2/core/beans/factory-scopes.html).
- [Framework 6.2 transaction propagation](https://docs.spring.io/spring-framework/reference/6.2/data-access/transaction/declarative/tx-propagation.html).
- [Framework 6.2 transactional annotations](https://docs.spring.io/spring-framework/reference/6.2/data-access/transaction/declarative/annotations.html).
- [Framework 6.2 cache annotations](https://docs.spring.io/spring-framework/reference/6.2/integration/cache/annotations.html).
- [Boot 3.5 system requirements](https://docs.spring.io/spring-boot/3.5/system-requirements.html).
