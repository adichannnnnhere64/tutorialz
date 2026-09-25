## Understand

A database transaction groups changes into a commit or rollback boundary. Atomicity does not imply that two arbitrary databases, a broker and an HTTP call are automatically coordinated. Decide which resources participate, which manager owns the transaction, and how recovery works.

JDBC auto-commit usually commits each statement independently. A local multi-statement transaction disables auto-commit, commits on success and rolls back on failure. Return pooled connections promptly and restore connection state according to the pool's contract. Container-managed/JTA work should use the container's transaction boundary rather than manual connection commits.

Isolation controls what concurrent operations can observe. Names alone are not sufficient: databases differ in implementation. Protect invariants using database constraints and deliberate locking or version checks. A check-then-insert sequence without a uniqueness constraint can race.

## Apply

For a payment operation, first record an idempotency key with a unique constraint in the same transaction as the payment update. A retry with that key must reuse the recorded result instead of charging again. If publishing an event must survive a crash, write an outbox row in the same database transaction and let a relay publish it afterward. Consumers still need deduplication because a relay may resend.

Use bound SQL values:

```sql
SELECT id, total FROM invoice
WHERE tenant_id = ? AND id = ?
```

A PreparedStatement binds these values separately from SQL syntax. Parameters cannot safely substitute arbitrary column names; choose identifiers from an allowed set.

## Cheatsheet

| Boundary | Meaning |
| --- | --- |
| REQUIRED | Join the existing transaction or create one |
| REQUIRES_NEW | Suspend the caller's transaction and run another |
| MANDATORY | Reject a call without an existing transaction |
| Savepoint | Partial local rollback, not an independent committed transaction |
| XA / two-phase commit | Coordinated resources with recovery obligations, not arbitrary HTTP atomicity |
| Flush / commit | Send pending statements / finish the transaction |
| Connection pool | Bound concurrent database access; more application threads do not create capacity |

## Check yourself

The database commits, then the process crashes before sending a JMS event. Does placing both calls in one Java method make them atomic?

**Answer:** No. The resources need an actual coordination strategy. An outbox solves the durable publication gap using one local database commit; XA is a different choice when the resources and runtime support it.

## Sources

[JDBC transactions](https://docs.oracle.com/javase/tutorial/jdbc/basics/transactions.html) · [Jakarta Transactions](https://jakarta.ee/specifications/transactions/2.0/) · [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
