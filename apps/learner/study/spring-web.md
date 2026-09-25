## Understand

### Boot assembles; Spring supplies the framework

Spring Boot combines dependency management, starters, auto-configuration, external configuration, and operational integration. It does not replace Spring's container or eliminate the need to understand the beans being created. This chapter targets Boot 3.5, Spring Framework 6.2, Java 17 or later, and Jakarta namespaces. Boot 4 and Framework 7 are separate upgrade targets, not interchangeable documentation baselines.

A starter is a convenient dependency set. Auto-configuration registers infrastructure when its conditions match, often considering classpath types, existing beans, properties, and application kind. A user bean can cause a conditional default to back off. That is intentional extensibility, but an accidentally scanned configuration can therefore change behavior. Inspect the conditions report and actual bean graph before adding duplicate infrastructure manually.

Use a coherent Boot dependency-management baseline. Overriding a single transitive library to fix a defect may be necessary, but it creates a compatibility decision that needs tests. Combining arbitrary Spring module versions is not a reliable way to obtain selected new features. Package scanning also has boundaries: a component outside the application's scan roots will not become a bean merely because its class exists in the JAR.

### HTTP request processing

Spring MVC runs on the Servlet stack. DispatcherServlet coordinates handler lookup, binding, controller invocation, and response handling. Filters run at the servlet boundary; handler interceptors operate in MVC's handler workflow. Authentication and authorization belong in a deliberate security layer, not in a collection of inconsistently applied controller checks.

RestController combines controller registration with response-body semantics. A plain Controller may return a view name instead. Message converters translate request and response bodies according to type and media type. Malformed JSON, a failed constraint, an unsupported media type, and a missing resource are different failures and should not all become a generic internal-server error.

### Configuration is an input boundary

Externalized configuration permits one artifact to run in different environments. The effective value follows property-source precedence, not simply whichever application.properties file a developer opened. Environment variables can override config data, and command-line options normally override both. Test-specific sources have their own precedence. Use typed, validated configuration objects for related settings, and fail early when required production values are absent or invalid.

Profiles select configuration variations; they are not authorization controls or a secret store. Avoid silently enabling permissive development behavior when a production variable is missing. Keep credentials outside committed files, apply least privilege to their storage, and ensure diagnostic endpoints do not reveal resolved secrets. Record nonsecret effective settings for troubleshooting without dumping every environment value.

## Apply

### Example W1: Bind an identifier without trusting it

Framework fragment for Spring MVC 6.2. OrderService and OrderView are application types, not framework classes.

```java
@RestController
@RequestMapping("/orders")
class OrdersApi {
  private final OrderService service;
  OrdersApi(OrderService service) { this.service = service; }

  @GetMapping("/{id}")
  OrderView find(@PathVariable("id") long id) {
    return service.findVisibleOrder(id);
  }
}
```

Binding a long proves only that the supplied text can become a number. The service must verify the authenticated caller's access to that particular order, including tenant boundaries. A valid identifier is not a permission. Return a transport projection rather than a persistence entity so serialization does not accidentally expose fields or trigger uncontrolled lazy database access.

### Example W2: Validate a body at the boundary

Framework fragment with Jakarta Validation 3.0 and Spring MVC 6.2; it requires a validation provider and a configured controller context.

```java
record CreateOrder(
    @jakarta.validation.constraints.NotBlank String customerReference,
    @jakarta.validation.constraints.Positive int quantity) {}

@RestController
class CreateOrdersApi {
  @PostMapping("/orders/validate")
  String validate(@jakarta.validation.Valid @RequestBody CreateOrder input) {
    return "accepted:" + input.quantity();
  }
}
```

These constraints reject a blank reference or nonpositive quantity after successful binding. They do not prove that the customer exists, that stock is available, or that the caller can buy on that account. Those rules belong in an authorized business operation with appropriate concurrency control. The endpoint is a validation illustration, not an order-placement implementation.

### Example W3: Trace an override

Illustrative configuration and launch arguments, not commands to run against a production service.

```properties
# packaged application.properties
server.port=8080
spring.lifecycle.timeout-per-shutdown-phase=20s
```

With SERVER_PORT=9090 in the environment and --server.port=7070 on the command line, the ordinary Boot precedence rules select 7070, assuming command-line property processing has not been disabled and no higher-priority test source is involved. The shutdown-phase timeout bounds each lifecycle phase; it is not automatically an end-to-end orchestrator termination budget.

The worked diagnosis is to inspect the actual property origin, then the deployed command and environment, rather than repeatedly editing the packaged file. A container platform or service wrapper may supply arguments unknown to the developer. Keep one authoritative place for production overrides and document intentional exceptions.

### Example W4: Translate a missing resource

Framework fragment for centralized MVC error handling.

```java
@RestControllerAdvice
class ApiErrors {
  @ExceptionHandler(OrderMissing.class)
  org.springframework.http.ProblemDetail missing(OrderMissing failure) {
    return org.springframework.http.ProblemDetail.forStatusAndDetail(
        org.springframework.http.HttpStatus.NOT_FOUND, "Order was not found");
  }
}
```

OrderMissing is an application exception. The response deliberately avoids including raw exception messages, SQL, paths, or internal stack traces. In a real API, decide whether absent and inaccessible resources should be indistinguishable to avoid disclosing existence. Include a safe correlation identifier in the error contract and log internal details separately under controlled access.

## Advanced

### Conditional configuration and bean ordering

Conditional-on-missing-bean checks depend on which bean definitions are known when the condition is evaluated. Auto-configuration ordering is about registering configurations, not necessarily the runtime initialization order of all their beans. Use explicit dependencies and documented extension points rather than relying on incidental classpath scanning order. A conditions report can explain why a configuration matched, failed, or backed off.

When several implementations exist, use qualifiers or an intentional primary candidate. Naming a bean to override a framework default is a different mechanism from supplying a bean that causes backoff. Enabling overriding globally can hide accidental duplicate definitions. In tests, assert the selected implementation and relevant conditions rather than only checking that the application context starts.

### Validation layers and error taxonomy

Bean Validation evaluates declared constraints; binding turns external representations into Java values; authorization decides whether an actor may perform an operation. Keep those responsibilities distinguishable. A class-level validation rule can enforce a relationship between fields, while a database uniqueness constraint still protects against concurrent requests that both pass an earlier availability check.

Spring MVC 6.2 has built-in method-validation support with different exception paths depending on where constraints are declared. Parameter-level constraints and an @Valid body are not always the same path. Class-level @Validated can involve proxy-based method validation. Test the actual exception type and response mapping for the selected version instead of assuming one handler catches every constraint failure.

### MVC, WebFlux, and asynchronous boundaries

WebFlux has a reactive execution model; returning a reactive type does not make blocking JDBC nonblocking. Blocking an event-loop thread can delay unrelated requests. MVC can also use asynchronous request processing, which releases the original request thread while work completes elsewhere, but the task still consumes resources and needs a deadline.

Choose the model based on the whole dependency chain and operational needs. A conventional MVC application with well-bounded blocking dependencies may be clearer than a partially reactive stack that repeatedly bridges to blocking code. When crossing asynchronous boundaries, security context, trace context, locale, and transaction assumptions need explicit handling. A thread-bound transaction does not automatically follow arbitrary tasks.

### Testing slices and observability

A web slice test isolates controller concerns such as routing, JSON binding, validation, and exception mapping. It deliberately does not prove full database wiring, migrations, commit behavior, or broker delivery. A full application test can cover those connections but still needs representative dependencies and failure scenarios. Use focused tests for speed and integration tests for boundaries that isolation cannot validate.

Observability combines useful metrics, traces, and logs. Label metrics by bounded categories, such as route templates and outcome classes, rather than raw user IDs or URLs containing identifiers. High-cardinality labels consume resources and can leak sensitive values. Traces should show dependency waits and failures while respecting privacy. Actuator availability is not a reason to expose every management endpoint publicly.

## Production

### Startup and shutdown are workflows

Validate required configuration during startup and make readiness reflect whether the instance can accept useful work. Liveness should answer whether restarting the instance is appropriate, not simply whether every remote dependency is healthy. Marking all instances unhealthy because one shared database is briefly unavailable can create a restart cascade.

Graceful shutdown stops or rejects new traffic according to the server integration and allows in-flight work time to finish. Coordinate server draining, load-balancer propagation, executor shutdown, and the platform's termination deadline. An application-level twenty-second timeout is ineffective if the platform kills the process after five seconds. Background tasks and messaging consumers need their own stop and acknowledgement policies.

### Keep persistence and transport separate

Avoid treating open persistence context during response serialization as an unexamined convenience. Serialization-triggered queries can hide N+1 behavior and make database load depend on JSON traversal. Fetch the required data deliberately and return a bounded DTO. Request pagination, body-size limits, and maximum query complexity are capacity controls, not just interface preferences.

For an incident where controllers are fast locally but slow in production, measure queueing, connection acquisition, SQL duration, downstream calls, and serialization. Do not infer that increasing the HTTP thread pool fixes the bottleneck. If a deployment fails only under a production profile, compare effective configuration origins and bean conditions before changing business code.

## Exam reasoning

### Follow one request through the layers

Identify how the request is routed, how data is bound, which validation applies, where authorization happens, what transaction surrounds the business work, and how the result is serialized. Each step answers a different question. A successful controller test cannot prove a later transaction committed. A NotNull annotation on an ID cannot authorize access to its resource.

For configuration questions, list the actual sources and compare precedence for the declared Boot version. For auto-configuration, identify the failed condition instead of assuming Boot creates every possible component. For reactive questions, inspect the dependency being called rather than deciding from the controller's return type alone.

Prefer answers that preserve a stable external contract without leaking internals. A consistent client error for invalid input is useful; returning raw stack traces is not. A management health signal must fit its operational purpose. A graceful-shutdown answer must consider both application lifecycle and infrastructure timing.

## Cheatsheet

| Concern | Approach and limit |
| --- | --- |
| Starter | Dependency convenience, not runtime magic |
| Auto-configuration | Conditional beans; inspect the conditions report |
| Configuration precedence | Effective source wins, not the file most recently edited |
| ConfigurationProperties | Typed related settings with validation |
| RestController | Response-body semantics rather than view-name interpretation |
| @Valid body | Structural constraints, not business authorization |
| RestControllerAdvice | Consistent safe error mapping |
| MVC slice | HTTP boundary tests, not database commit proof |
| WebFlux | Do not block event loops with ordinary JDBC |
| Actuator | Deliberate endpoint exposure and authorization |
| Metrics | Bounded labels; avoid raw customer identifiers |
| Readiness / liveness | Accept traffic / restart usefulness |
| Graceful shutdown | Coordinate drain, tasks, and platform timeout |

## Check yourself

### 1. Missing component

Why might a custom repository bean stop an auto-configured default from appearing?

**Answer:** A conditional-on-missing-bean rule may intentionally back off. Inspect the conditions report and selected bean rather than assuming startup silently lost the default.

### 2. Valid identifier

Does successful long conversion of an order ID establish access rights?

**Answer:** No. It validates representation only. Authorization must check the caller's right to the specific resource and tenant.

### 3. Configuration conflict

Packaged port 8080, environment port 9090, command-line port 7070: which normally wins?

**Answer:** 7070, assuming ordinary Boot processing and no higher-priority test override. Verify effective property origins when diagnosing a real deployment.

### 4. Advanced: slice limits

An MVC slice passes, but production fails on a deferred database constraint. What is missing?

**Answer:** A persistence integration test that reaches actual commit with representative schema and migrations. Controller isolation does not exercise that boundary.

### 5. Advanced: reactive blocking

Does wrapping a blocking JDBC call in a reactive return type make it nonblocking?

**Answer:** No. The underlying call still blocks its executing thread. Choose an appropriate execution model and bounded scheduling strategy, or a genuinely nonblocking dependency.

### 6. Advanced: shutdown budget

Why can a twenty-second shutdown phase still lose in-flight work?

**Answer:** The platform may terminate the process sooner, or load balancing and background-task lifecycles may not be coordinated. Align the full shutdown sequence and test it under load.

## Sources

Reviewed 2026-09-25. Baseline: Boot 3.5, Framework 6.2, Java 17+, Jakarta Validation 3.0. Framework fragments require application wiring.

- [Boot auto-configuration](https://docs.spring.io/spring-boot/3.5/reference/using/auto-configuration.html)
- [External configuration precedence](https://docs.spring.io/spring-boot/3.5/reference/features/external-config.html)
- [Spring MVC](https://docs.spring.io/spring-framework/reference/6.2/web/webmvc.html)
- [MVC validation](https://docs.spring.io/spring-framework/reference/6.2/web/webmvc/mvc-controller/ann-validation.html)
- [MVC error responses](https://docs.spring.io/spring-framework/reference/6.2/web/webmvc/mvc-ann-rest-exceptions.html)
- [Boot testing](https://docs.spring.io/spring-boot/3.5/reference/testing/index.html)
- [Boot observability](https://docs.spring.io/spring-boot/3.5/reference/actuator/observability.html)
- [Graceful shutdown](https://docs.spring.io/spring-boot/3.5/reference/web/graceful-shutdown.html)
