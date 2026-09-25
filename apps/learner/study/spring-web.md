## Understand

Spring Boot assembles a configured application using starters, auto-configuration and external properties. Auto-configuration depends on classpath contents, properties and existing beans; inspect the conditions report when an expected component is absent. Pin a coherent dependency/BOM version instead of combining unrelated library releases.

Spring MVC maps incoming HTTP requests to controller operations. `@RestController` writes response bodies; a conventional `@Controller` may return a view name. Bind path, query and body data deliberately. Keep business rules in services, not duplicated across controllers.

These examples target Spring Boot 3 with Spring Framework 6 and Jakarta imports. Do not mix old `javax.validation` or `javax.servlet` dependencies into that stack. The `javax` packages provided by Java SE, such as `javax.sql`, do not all change to `jakarta`.

## Apply

Controller fragment with an injected service:

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

Here OrderService and OrderView are application types. The service must enforce which orders the authenticated caller may access. An ID in a path is not authorization. Translate expected failures through a consistent exception handler and avoid exposing internal stack traces.

## Cheatsheet

| Need | Approach |
| --- | --- |
| Request body constraints | `@Valid` plus appropriate Jakarta Bean Validation constraints |
| Configuration | Properties/environment and validated configuration objects; no committed secrets |
| Environment differences | Profiles with explicit production settings, not implicit laptop defaults |
| Controller tests | MVC-focused tests for binding, status and error handling |
| Full wiring | Integration test with representative database/broker configuration |
| Observability | Metrics and health endpoints with deliberate exposure and authorization |
| MVC vs WebFlux | Choose execution and blocking behavior deliberately; reactive return types alone do not fix blocking I/O |

## Check yourself

An MVC slice test passes while real database commits fail. What test is missing?

**Answer:** An integration test of the transaction and actual persistence boundary, including commit-time constraints and production-like migrations. Controller isolation tests do not exercise those components.

## Sources

[Spring MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html) · [Boot external configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html) · [Boot testing](https://docs.spring.io/spring-boot/reference/testing/index.html)
