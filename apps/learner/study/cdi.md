## Understand

### CDI manages dependencies and contextual lifetimes

Jakarta Contexts and Dependency Injection resolves dependencies by bean type and qualifiers, then manages their contextual lifecycle. An injection point is a declaration of a required contract. The container must find a valid matching bean after discovery, alternatives, and resolution rules are applied. No match is unsatisfied; unresolved multiple matches create ambiguity. A class existing on the classpath is not enough to make it discoverable or selected.

This chapter targets CDI 4.0 in Jakarta EE 10. CDI Lite and CDI Full are different feature sets. Lite supports core injection, scopes, interceptors, events, and build-compatible extensions, while Full adds facilities including decorators, passivating scopes, and portable extensions. A framework claiming Lite support is not promising every Full feature. Check the actual runtime and profile before relying on advanced integration.

Qualifiers are typed annotations that express which implementation is required. A payment gateway qualified for card payments is different from one qualified for bank transfer. Bean names are primarily useful for name-based integration such as EL, not a replacement for a well-defined injection contract. Alternative beans support deliberate deployment selection, and their activation must be explicit rather than accidentally controlled by classpath order.

### Scope is not synchronization

Request scope associates an instance with a request context. Application scope shares an instance across the application's context. Dependent scope associates a dependent instance's lifecycle with its owner or the programmatic lookup that created it. These are lifecycle rules, not thread-safety guarantees. An application-scoped service should not keep mutable per-request order data in its fields.

Normal-scoped references usually use a client proxy that locates the current contextual instance when invoked. Injecting a request-scoped bean into an application-scoped bean therefore does not necessarily capture one request forever. It does require an active context at invocation time. Calling the reference from an arbitrary background thread can fail or use the wrong assumptions if context propagation is not supported.

### Managed construction matters

Objects created directly with new are ordinary Java objects unless explicitly integrated through a supported container mechanism. An annotation on the class does not cause an independently constructed object to receive injection, lifecycle callbacks, interceptors, or automatic destruction. Constructor injection makes dependencies visible, but the container still needs to own construction for its services to apply.

Producers adapt objects whose creation needs custom logic, including third-party types. Disposers define cleanup for produced objects at their managed destruction point. Decide whether the producer creates an owned resource or merely exposes a reference owned elsewhere. Closing a shared container resource in an inappropriate disposer can break other consumers; omitting cleanup for an owned resource leaks it.

## Apply

### Example C1: Resolve a qualified dependency

CDI 4.0 fragment; PaymentGateway is an application interface and the matching bean must be discoverable.

```java
@jakarta.inject.Qualifier
@java.lang.annotation.Retention(java.lang.annotation.RetentionPolicy.RUNTIME)
@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE,
    java.lang.annotation.ElementType.FIELD, java.lang.annotation.ElementType.PARAMETER,
    java.lang.annotation.ElementType.METHOD})
@interface CardPayments {}

@jakarta.enterprise.context.ApplicationScoped
class Checkout {
  @jakarta.inject.Inject
  @CardPayments
  PaymentGateway gateway;
}
```

The qualifier belongs on both the injection requirement and its intended bean or producer. Adding it only to the field without a matching bean changes ambiguity into an unsatisfied dependency. Checkout is application-scoped, so the gateway's own lifecycle and concurrency contract also matter. Field injection is shown for brevity; constructor injection can make the dependency explicit in ordinary Java tests.

### Example C2: Produce a deterministic clock

CDI fragment for a simple reusable service dependency.

```java
@jakarta.enterprise.context.ApplicationScoped
class TimeServices {
  @jakarta.enterprise.inject.Produces
  @jakarta.enterprise.context.ApplicationScoped
  java.time.Clock clock() {
    return java.time.Clock.systemUTC();
  }
}
```

Application code can inject Clock instead of reading wall-clock time internally. Tests can select an alternative producer returning a fixed clock. The produced bean's scope is declared on the producer; the declaring class's scope is a separate lifecycle. Clock is thread-safe and does not require disposal. A produced network client would need a deliberate shutdown policy rather than copying this example unchanged.

### Example C3: Observe a committed business event

CDI Full/Jakarta transaction integration fragment; OrderPlaced is an application event value.

```java
class OrderObservers {
  void committed(@jakarta.enterprise.event.Observes(
      during = jakarta.enterprise.event.TransactionPhase.AFTER_SUCCESS)
      OrderPlaced event) {
    recordMetric(event);
  }
}
```

The observer is intended for notification after a successful active transaction. If no transaction is active, transactional observer rules allow immediate notification, so firing location matters. This callback is not a durable message queue. A process crash can prevent an in-memory observer from performing an external effect after the database commits. Use an outbox when reliable publication is required.

The containing class must be discovered as a bean, and recordMetric is an application method. Choose a bean-defining scope or appropriate archive configuration in the actual implementation. The fragment illustrates event timing, not a complete registration or metrics subsystem.

### Example C4: Match a producer with its disposer

Illustrative CDI resource fragment; ReportClient is an application AutoCloseable type.

```java
@jakarta.enterprise.inject.Produces
ReportClient reportClient() {
  return new ReportClient();
}

void closeClient(@jakarta.enterprise.inject.Disposes ReportClient client)
    throws Exception {
  client.close();
}
```

The producer has dependent scope unless another scope is declared. The disposer matches the produced type and qualifiers, and cleanup occurs when the container destroys that contextual instance. This example assumes the producer owns the client. Do not manually close an injected shared instance early or create the client outside CDI and expect this disposer to run.

## Advanced

### Resolution, discovery, and alternatives

Bean discovery rules depend on archive metadata and bean-defining annotations. CDI 4.0 changed defaults relative to older configurations, so inspect beans.xml and the actual version rather than relying on historical empty-file behavior. Discovery and injection resolution are separate steps: a correctly qualified class that was never discovered cannot satisfy an injection point.

Qualifier members participate in matching unless marked Nonbinding. This is useful when annotation metadata configures behavior without creating a separate qualifier identity for every value. Alternatives can be enabled through supported deployment metadata or priority rules. Keep test replacements from leaking into production by making their activation visible and testable.

Programmatic Instance lookup supports selection and iteration when resolution must happen dynamically. It should not become a service locator that hides every dependency. Check unsatisfied or ambiguous states where appropriate, and destroy dependent instances according to ownership. Repeated lookup of dependent resources without destruction can leak memory or connections even though field injection elsewhere is well managed.

### Proxies and inactive contexts

Normal scopes use proxyable bean types under the specification's rules. Final classes, unsuitable constructors, and final methods can affect proxyability; implementations may offer extensions, but portable code should not silently depend on them. A proxy reference is not a reason to compare contextual objects by concrete implementation class or identity in business logic.

Calling a request-scoped collaborator after the request finishes does not restore its context. Extract an immutable work command containing only necessary data and submit it through a managed execution design with defined security and transaction behavior. Activating a fresh request context for a task, where supported, is not the same as copying the original user's entire request or identity.

### Interceptors versus decorators

An interceptor applies a cross-cutting concern such as timing, auditing, or transaction handling through an interceptor binding and container invocation. A decorator implements a business interface and delegates to another implementation while adding domain-specific behavior. Both need enablement and ordering according to the runtime's rules; declaring a class alone may not activate it.

Do not assume direct self-invocation is a portable intercepted boundary. Calls through the appropriate managed reference are the reliable design point for container services. Avoid putting essential correctness solely in a private helper annotation that the container never intercepts. Test actual container invocation paths, especially when combining CDI, Enterprise Beans, and framework-specific proxies.

### Events, async observers, and passivation

Synchronous events decouple type-based notification but still participate in the caller's execution and failure behavior. Async observers use a different notification path; contexts, exception delivery, ordering, and transaction assumptions differ. Neither event mode automatically provides persistence, cross-node delivery, or replay after restart. Use a broker or durable database workflow when those are required.

Passivating scopes, such as session scope in CDI Full, require passivation-capable state and dependencies. Serializing a graph containing a nonserializable dependent resource may fail or be rejected during validation. A live socket, persistence context, or request object is not suitable conversational state merely because its holder implements Serializable. Store stable identifiers and reconstruct transient resources through managed services.

## Production

### Make container errors actionable

Treat deployment-time injection failures as useful diagnostics. Report the injection point, required type, qualifiers, discovered candidates, and archive configuration. Do not “fix” ambiguity by deleting an implementation that another feature needs or renaming classes until startup happens to succeed. Express the intended selection in the dependency model.

Add startup tests for critical qualifiers, alternatives, and producer scopes. A plain unit test using new Checkout can test business logic with explicit collaborators but does not validate CDI wiring. Run a container-backed integration test for discovery, interception, disposal, and context behavior. Verify application shutdown closes owned resources once and does not close shared external resources prematurely.

### Keep asynchronous work explicit

At an async boundary, capture the authenticated operation's authorized inputs, not arbitrary mutable request objects. Re-check authorization if the action executes later under changed conditions. Record an operation ID for tracing and cancellation. A CDI event called after commit can be useful for local metrics but should not be the only record of a required invoice email or external settlement instruction.

For application-scoped caches, define tenant-aware keys, concurrency, eviction, and invalidation. The scope annotation supplies sharing, not a complete cache design. For session state, test concurrent tabs, failover, serialization, and expiry. Keep bean lifetimes aligned with the resources they own so cleanup and recovery are understandable during incidents.

## Exam reasoning

### Resolve the bean before predicting behavior

Start with discovery, then bean types, qualifiers, enabled alternatives, and ambiguity resolution. Only after a valid bean is selected should you reason about scope, proxying, and invocation. A class name that sounds correct is irrelevant if its qualifiers do not match.

For lifecycle questions, distinguish the producer method's declaring bean from the produced bean. For cleanup, identify who owns the resource and when that contextual instance is destroyed. For interceptor questions, verify a managed invocation. For events, ask whether notification is synchronous, asynchronous, transaction-phased, or durable; these are different guarantees.

For portability, identify Lite versus Full and the Jakarta EE profile. A feature working in one implementation through an extension is not necessarily part of the selected standard. Choose the answer that explicitly satisfies the required contract instead of assuming every annotation triggers every container service.

## Cheatsheet

| Need | CDI mechanism and boundary |
| --- | --- |
| Dependency selection | Type plus qualifiers |
| Ambiguity | Resolve with deliberate qualifiers or enabled alternative |
| Request lifetime | Request context must be active when used |
| Shared service | Application scope does not imply thread safety |
| Dependent bean | Lifecycle belongs to owner or lookup handle |
| Custom construction | Producer with explicit produced scope |
| Owned resource cleanup | Matching disposer and managed destruction |
| Cross-cutting concern | Interceptor binding and managed invocation |
| Business-interface augmentation | Decorator; CDI Full feature |
| Local notification | Event, not automatically durable messaging |
| After commit | Transactional observer; no-transaction case matters |
| Session passivation | Serializable/passivation-capable graph |
| Lite versus Full | Check supported feature set and extensions |

## Check yourself

### 1. Two gateways

Two beans satisfy an injection point. Does classpath order select the winner?

**Answer:** Not as a valid portable resolution strategy. Use qualifiers or a deliberately enabled alternative so resolution is unambiguous.

### 2. Shared scope

Does ApplicationScoped make a mutable counter atomic?

**Answer:** No. Scope defines contextual lifetime and sharing. Concurrent updates still require synchronization or an appropriate atomic operation.

### 3. Producer scope

Does an application-scoped producer class automatically make every produced object application-scoped?

**Answer:** No. The produced bean has its own scope, defaulting to dependent when no scope is declared on the producer.

### 4. Advanced: context escape

Can a request-scoped reference safely be used after the request on any new thread?

**Answer:** No. Its contextual instance requires an active appropriate context. Use an explicit managed task design and immutable inputs rather than retaining request-bound state.

### 5. Advanced: durable observer

Does AFTER_SUCCESS guarantee an external notification survives a process crash?

**Answer:** No. It controls observer timing, not durable delivery. Persist an outbox intent with the business transaction when the notification must be recoverable.

### 6. Advanced: Lite deployment

Can a CDI Full decorator be assumed available in every CDI Lite implementation?

**Answer:** No. Lite is a defined subset. Select a supporting runtime or redesign using features within the required compatibility boundary.

## Sources

Reviewed 2026-09-25. Baseline: CDI 4.0 / Jakarta EE 10, with Lite and Full distinctions explicit. Fragments require container discovery and application types.

- [CDI 4.0 specification](https://jakarta.ee/specifications/cdi/4.0/jakarta-cdi-spec-4.0.html)
- [CDI 4.0 API](https://jakarta.ee/specifications/cdi/4.0/apidocs/)
- [Jakarta Dependency Injection](https://jakarta.ee/specifications/dependency-injection/2.0/)
- [Jakarta Interceptors](https://jakarta.ee/specifications/interceptors/2.1/)
- [CDI tutorial](https://jakarta.ee/learn/docs/jakartaee-tutorial/current/cdi/cdi-basic/cdi-basic.html)
- [Jakarta Transactions](https://jakarta.ee/specifications/transactions/2.0/)
