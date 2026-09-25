## Understand

Hibernate ORM implements Jakarta Persistence and adds provider-specific features. An EntityManager/Session persistence context tracks managed entities. New objects are transient; managed objects participate in dirty checking; detached objects are outside that context; removed objects are scheduled for deletion. `merge` copies state into a managed instance and returns that instance; it does not turn the supplied object into the managed instance.

Mapping access is usually determined by where `@Id` is placed. With field access, put mapping annotations—including `@Transient`—on fields. A getter annotation does not exclude its backing field. Keep both ends of bidirectional associations consistent in application code; update the owning side that controls the foreign key.

`flush` synchronizes pending changes but does not itself commit. Lazy loading needs an appropriate live context; eager mapping is not a universal N+1 fix. Choose a fetch join, entity graph, projection or measured batch strategy for the use case.

## Apply

Hibernate/JPA entity fragment:

```java
@Entity
class Invoice {
    @Id @GeneratedValue Long id;
    @Version long version;
    BigDecimal total;
    @Transient String displayHint;
    protected Invoice() {}
}
```

Assume Jakarta Persistence imports, BigDecimal and a compatible schema. The version participates in optimistic conflict detection. Handle a stale update at the transaction/use-case boundary rather than blindly overwriting newer data. Pessimistic locking instead acquires database locks and requires short transactions and timeout planning.

## Cheatsheet

| Need | Rule / diagnostic |
| --- | --- |
| Schema managed by migrations | `hibernate.hbm2ddl.auto=validate`; do not use create/update as production migration strategy |
| SQL vs parameters in ORM 6.6 | `org.hibernate.SQL` DEBUG; `org.hibernate.orm.jdbc.bind` TRACE for controlled diagnostics |
| Orphan removal | Disassociating a privately owned child can delete it; distinct from cascading parent removal |
| First-level cache | Persistence-context identity; second-level cache is a separate optional mechanism |
| Collection fetch + pagination | Watch row multiplication and in-memory pagination; consider IDs then bounded fetch |
| Hibernate 6.6 soft deletion | ORM filtering does not rewrite arbitrary JDBC SQL; handwritten queries need the indicator predicate |
| Records | Modern embeddable support is version-specific; do not assume an ordinary entity can be a record |

## Check yourself

Why can a query work inside a service but fail when the JSP accesses a relation afterward?

**Answer:** The relation was lazy and its persistence context is closed. Fetch the view's required data inside the transaction or return a projection with those values.

## Sources

[Hibernate 6.6 introduction](https://docs.hibernate.org/orm/6.6/introduction/html_single/) · [Fetching and mapping guide](https://docs.hibernate.org/orm/6.6/userguide/html_single/) · [ORM logging](https://docs.hibernate.org/orm/6.6/logging/logging.html) · [Jakarta Persistence](https://jakarta.ee/specifications/persistence/3.2/)
