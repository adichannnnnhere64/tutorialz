## Understand

Jakarta CDI resolves injected dependencies by bean type and qualifiers. `@Inject` declares the injection point. Qualifiers distinguish multiple implementations; a name or classpath presence alone does not fix an ambiguous dependency. Producers expose objects created through custom factory logic, and disposers support cleanup of produced resources.

Scopes describe contextual lifetimes. Request scope belongs to one request; application scope is shared; dependent scope ties an instance to its owning injection target. Normal scopes generally use client proxies. Session-scoped passivation needs compatible serializable state and dependencies.

Interceptors add cross-cutting behavior through container interception. Decorators augment a specific business interface. CDI events decouple publishers and observers; transaction-phase observers make timing explicit. Alternatives let a deployment deliberately select another implementation.

## Apply

Injection fragment:

```java
@ApplicationScoped
class Checkout {
    private final PaymentGateway gateway;
    @Inject
    Checkout(@CardPayments PaymentGateway gateway) {
        this.gateway = gateway;
    }
}
```

`CardPayments` is an application-defined CDI qualifier annotation, and the matching bean must carry it. Discovery and bean-defining annotations must be configured for the selected CDI version/runtime. Since Checkout is application-scoped, avoid holding per-request order state in its fields.

## Cheatsheet

| Requirement | CDI concept |
| --- | --- |
| Disambiguate implementation | Qualifier on bean and injection point |
| Construct third-party object | Producer method/field and appropriate disposal |
| Wrap technical concerns | Interceptor binding and enabled interceptor |
| Extend business contract | Decorator with a delegate injection point |
| Notify after successful transaction | Transactional observer at the required phase |
| Test/deployment replacement | Selected alternative; keep activation explicit |
| Context active only on request thread | Do not assume it follows arbitrary new threads |

Creating a class with `new` does not automatically give it injected fields, intercepted methods or a managed lifecycle. Scope annotations on the class cannot manage an independently constructed object.

## Check yourself

Two PaymentGateway beans satisfy an unqualified injection point. Why is choosing by implementation class name at runtime a weak fix?

**Answer:** The container must resolve the injection during its dependency analysis. A qualifier expresses the required implementation in that model and makes ambiguity a deployment-time issue.

## Sources

[CDI 4.1 specification](https://jakarta.ee/specifications/cdi/4.1/) · [CDI tutorial](https://jakarta.ee/learn/docs/jakartaee-tutorial/current/cdi/cdi-basic/cdi-basic.html)
