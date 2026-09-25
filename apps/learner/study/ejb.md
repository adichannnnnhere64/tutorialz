## Understand

Jakarta Enterprise Beans provides managed business components with services such as transactions, authorization and scheduling. A stateless session bean does not retain a client's conversation between calls. A stateful reference identifies one conversation. A singleton bean shares one instance within its application scope, with container-managed concurrency by default.

A stateful bean is not automatically one instance per HTTP session. Keep a separate reference for each conversation and remove it when finished. Sharing one reference through an application-wide registry shares that conversation. A singleton annotation or write lock does not elect one owner across independent server JVMs.

The container applies transaction attributes at managed invocation boundaries. REQUIRED joins or starts a transaction; REQUIRES_NEW suspends the caller's transaction; MANDATORY rejects a call without one. Checked application exceptions and system exceptions have different rollback rules; state the intended application-exception behavior explicitly.

## Apply

Business-interface invocation into this bean requires an existing transaction:

```java
@Stateless
public class Settlement {
    @TransactionAttribute(TransactionAttributeType.MANDATORY)
    public void settle() {
        // Apply changes to resources participating in the caller transaction.
    }
}
```

Assume Jakarta Enterprise Beans imports and a compatible server. Calling through a local business view without a transaction is rejected before the method executes. Merely constructing Settlement with `new` does not create a managed enterprise bean.

## Cheatsheet

| Mechanism | Remember |
| --- | --- |
| `@Asynchronous` | Caller transaction does not propagate to the asynchronous invocation |
| `@RunAs` | Identity for outgoing calls; does not replace inbound caller authorization |
| `@RolesAllowed` | Declare roles and verify deployment mappings |
| Portable JNDI | `java:global/app/module/Bean!fully.qualified.Interface` |
| `@Lock(WRITE)` | Serializes singleton access in its scope, not across independent nodes |
| Message-driven bean | Container-managed asynchronous message processing; inspect activation properties |
| Nonpersistent timer | Lifetime/persistence choice, not cluster-wide leader election |

## Check yourself

Three independently deployed nodes each run a singleton's daily timer. How do you stop duplicate settlement?

**Answer:** Establish execution ownership through a coordinated scheduler or durable claim, and make the operation safe to retry. A local singleton lock cannot coordinate another JVM. Test recovery when a node fails after acquiring the claim.

## Sources

[Enterprise Beans 4.0](https://jakarta.ee/specifications/enterprise-beans/4.0/) · [Session bean tutorial](https://jakarta.ee/learn/docs/jakartaee-tutorial/current/entbeans/ejb-intro/ejb-intro.html)
