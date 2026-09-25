## Understand

Spring's container creates and connects beans. Constructor injection makes required dependencies explicit. Register application components using scanning annotations or `@Bean` methods. Resolve multiple candidates with `@Qualifier` or an appropriate `@Primary` choice. A stereotype alone does not ensure the package is scanned.

Singleton is the default bean scope and applies per container. A prototype injected once into a singleton remains that one injected object; use a provider lookup when each operation needs a new instance. Spring scope does not make mutable state thread-safe.

These notes use Spring Framework 6.x/7.x semantics. In proxy mode, AOP advice applies through the proxy. Calling `this.save()` bypasses proxy-based `@Transactional` advice. By default, unchecked exceptions trigger rollback and checked exceptions do not; explicit rules or newer global configuration can change this.

## Apply

In a Spring service, select the manager that owns the order data source:

```java
@Transactional(transactionManager = "ordersTx", rollbackFor = IOException.class)
public void importOrders() throws IOException {
    // Persist orders through repositories using the orders data source.
}
```

Assume transaction management is enabled and another bean calls this public method through its proxy. Merely choosing `REQUIRES_NEW` does not choose a transaction manager or coordinate a second database.

For `@Cacheable`, include every input affecting the result in the key. Tenant ID plus invoice ID avoids returning one tenant's invoice to another. Expiry or `sync=true` cannot repair a colliding key.

## Cheatsheet

| Mechanism | Common trap |
| --- | --- |
| `ObjectProvider.getObject()` | Lookup per operation for a fresh prototype |
| `@Configuration(proxyBeanMethods=false)` | Direct calls to bean factory methods are ordinary Java calls |
| `@Bean` method parameter | Explicitly inject another managed bean |
| Transactional tests | A rollback-only test can conceal failures at actual commit |
| AOT / native image | Register needed runtime hints; build-time analysis cannot discover arbitrary dynamic classes |
| Reactive transactions | Compose database work in the returned publisher; independent `subscribe()` loses that context |

## Check yourself

Why does `this.importOrders()` ignore the method's transaction annotation in proxy mode?

**Answer:** It invokes the target directly. Move the boundary to an externally invoked managed bean or otherwise deliberately use a supported interception arrangement.

## Sources

[Container overview](https://docs.spring.io/spring-framework/reference/core/beans/basics.html) · [Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html) · [Transactions](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html) · [Cache annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)
