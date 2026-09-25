## Understand

### A transaction protects a defined boundary

A transaction groups changes into an outcome that commits or rolls back within participating resources. Atomicity does not automatically include an email, an HTTP call, or a second database merely because they occur inside the same Java method. Identify the transaction manager, the enlisted resources, and the exact moment the outcome becomes durable. Returning from a repository method, flushing an ORM session, and successfully committing are different events.

JDBC connections normally begin in auto-commit mode. Each statement is committed according to the JDBC statement-completion rules unless auto-commit is disabled. With an explicitly owned local transaction, the application commits or rolls back on that connection. In a managed Jakarta or Spring transaction, the manager owns the boundary; do not mix manual connection commits with container-managed work. Mixing ownership creates behavior that is difficult to reason about and may be rejected.

ACID names useful properties, but each needs a concrete interpretation. Consistency means preserving the application's invariants through correct rules and constraints; the database cannot invent missing business rules. Isolation controls concurrent observations and effects. Durability depends on the selected database and storage configuration, not on receiving a success log before commit. Atomicity does not mean that every external observer sees every system update instantaneously.

### Isolation is about concurrent histories

Dirty reads observe uncommitted data. Nonrepeatable reads observe a changed row across reads. Phantom reads observe a changed matching set. Serialization anomalies include executions whose combined result cannot be explained by any serial transaction order. The usual isolation names define prohibited phenomena, but implementations can provide stronger guarantees or different mechanisms.

This chapter uses PostgreSQL 17 when describing a concrete database: its Read Uncommitted behaves as Read Committed, and its Repeatable Read prevents phantoms but can still permit serialization anomalies. Do not generalize that behavior to every database. MVCC reduces some reader/writer blocking but does not remove all locks or make all read-modify-write business logic safe.

### Connections are scarce resources

A DataSource usually gives access to connections, often through a pool. Closing a borrowed logical connection normally returns it to the pool rather than closing the physical database connection. Still close it: a leak reduces capacity until requests stall. Separate connection acquisition timeout, statement timeout, socket timeout, and the request's overall deadline. They protect different stages of the work.

## Apply

### Example D1: Conditional stock decrement

Illustrative SQL; bind the two parameters as a positive requested quantity and a product ID, and execute inside the application's transaction.

```sql
UPDATE inventory
SET available = available - ?
WHERE product_id = ? AND available >= ?;
```

Bind the requested quantity again to the third parameter. Check the affected-row count: one means the conditional update succeeded; zero means the product was absent or insufficient stock remained. This avoids a separate unprotected read followed by a write based on stale data. A database constraint can reinforce nonnegative stock. The full order workflow still needs its own transaction boundary and error policy.

A request quantity of negative five would increase stock under this statement, so positive-input validation is essential. SQL atomicity does not compensate for invalid input. If retrying after an unknown commit outcome, use a stable operation identity so the same order does not reserve inventory twice.

### Example D2: Parameterize values

JDBC method-body fragment; connection is an already owned connection and tenant/id come from validated, authorized application context.

```java
try (java.sql.PreparedStatement statement = connection.prepareStatement(
    "select total from invoice where tenant_id = ? and invoice_id = ?")) {
  statement.setString(1, tenant);
  statement.setLong(2, id);
  try (java.sql.ResultSet rows = statement.executeQuery()) {
    if (rows.next()) {
      java.math.BigDecimal total = rows.getBigDecimal(1);
      consume(total);
    }
  }
}
```

Values are bound separately from SQL text. The query includes tenant scope, but the caller must derive that scope from trusted authorization context, not simply accept an arbitrary tenant header. PreparedStatement parameters cannot stand in for arbitrary table names or sort directions; use a strict allowlist for dynamic identifiers. Resource closure is nested in ownership order.

### Example D3: Recover an optional step with a savepoint

Illustrative local JDBC transaction fragment; auto-commit is already false, and the driver/database support savepoints.

```java
java.sql.Savepoint beforeOptional = connection.setSavepoint();
try {
  insertOptionalAuditDetail(connection);
} catch (java.sql.SQLException failure) {
  connection.rollback(beforeOptional);
}
```

Rollback to the savepoint undoes work after that point while retaining earlier transaction work where the database supports recovery. It is not a separate committed transaction. The outer owner must still commit or roll back, and some errors make continued work inappropriate. Do not suppress audit failure if the audit is legally or operationally required; this example explicitly assumes an optional detail.

### Example D4: Couple an order and its event

Illustrative outbox workflow: in one database transaction, insert the order and an outbox row containing a stable event ID and payload. Commit them together. A separate relay reads committed rows, publishes to the broker, and records publication progress.

If the relay crashes after sending but before recording success, it sends again after restart. Therefore consumers must deduplicate or process idempotently. The outbox removes the gap between local business commit and durable intent to publish; it does not make delivery globally exactly once. Monitor pending age and relay failures, not just whether the relay process is running.

## Advanced

### Lost updates, write skew, and constraints

Two transactions reading a balance and then writing independently computed replacements can lose an update under insufficient coordination. An atomic conditional SQL update, optimistic version check, or appropriate lock can protect a row-level invariant. Pick the mechanism based on the actual invariant and expected contention rather than assuming one isolation label solves everything.

Write skew can involve different rows: two on-call doctors each observe another doctor available, then independently go off duty, leaving none. Row-version checks on separate rows may not detect the violated cross-row invariant. Serializable execution, explicit coordination on a shared resource, or a schema design that enforces the invariant may be needed. A repeated read returning a stable snapshot does not prove the overall decision is serializable.

Use unique, foreign-key, and check constraints as authoritative integrity barriers where they express the rule. An application-level existence check can improve an error message but cannot prevent a concurrent insert by itself. Handle the constraint's failure at the real transaction outcome. Deferred constraints may fail at commit even after every individual statement appeared successful.

### Deadlocks and retries

Transactions can deadlock by acquiring resources in inconsistent orders. Keep transactions short, lock shared resources in a consistent order, and inspect the database's deadlock report to identify the actual cycle. Simply increasing a timeout does not eliminate a cycle. Even well-designed systems should be prepared for transient deadlock or serialization failures under contention.

Retry the whole transaction from fresh reads when the database requires it, not only the final failed statement against stale decisions. Bound attempts, apply suitable backoff and jitter, and keep nontransactional effects out of the retried block or make them idempotent. Do not retry malformed SQL, permanent constraint violations, or authorization failures as if they were transient outages.

### Query plans, indexes, and batching

An index speeds certain access paths at the cost of storage and write maintenance. Composite index column order and predicates influence usefulness. A query plan depends on statistics, data distribution, parameter values, and available indexes; testing only a tiny development table can hide production behavior. Use EXPLAIN to inspect planning and EXPLAIN ANALYZE only with awareness that it executes the statement.

Batching reduces round trips but does not automatically bound a transaction's memory or lock lifetime. Separate batch size, fetch size, flush frequency, and commit frequency. Long transactions can retain row versions or locks and delay maintenance. Choose chunk boundaries that allow safe restart and describe whether partial completion is acceptable. “All records or none” and “resume a million-record import” may demand different designs.

### XA and local alternatives

Jakarta Transactions can coordinate XA-capable resources through a transaction manager. Two-phase commit asks participants to prepare before a global decision, and recovery must resolve prepared work after failure. This requires compatible drivers/providers, durable coordinator state, stable resource identity, and operational procedures. It is not enabled merely by adding an annotation to two ordinary connections.

XA coordinates participating resource outcomes, not arbitrary HTTP services or irreversible human actions. Heuristic outcomes and in-doubt transactions require incident handling rather than blind retries. An outbox and idempotent consumers often fit asynchronous integration, while a saga uses explicit compensating actions for longer workflows. These alternatives change consistency and recovery semantics; they are not drop-in synonyms for one ACID transaction.

## Production

### Size pools for the complete workload

A pool of fifty connections per instance across twenty replicas can demand one thousand database connections. Include deployment surges, background jobs, migrations, and administrative capacity in the budget. More connections may worsen contention and memory usage. Measure queue wait, utilization, transaction age, lock waits, and database saturation before changing limits.

Keep remote calls and slow user interaction outside a database transaction whenever possible. Holding a connection while waiting for an unrelated service increases contention and failure coupling. If a business flow needs remote confirmation, model intermediate state and reconciliation explicitly. Avoid holding locks while making calls whose latency and outcome you cannot control.

### Observe outcomes and recover deliberately

Log a safe operation ID, transaction outcome, and retry count rather than entire SQL parameters containing personal data. Distinguish failure before commit from an uncertain outcome caused by a connection loss during commit. In the latter case, the database may have committed even though the application saw an exception. Reconcile using a unique business key before repeating an irreversible operation.

Test crash points: before commit, after commit before response, after broker publish before outbox acknowledgement, and during rollback. Verify that connection state is reset by the pool and that transaction-bound resources do not escape their lifetime. Restore drills, migration rollback strategy, and reconciliation tooling are part of transaction reliability, not optional work after feature completion.

## Exam reasoning

### Draw boundaries and interleavings

List which statements belong to each transaction and which resources actually participate. Then write the competing read/write sequence. Ask which invariant can fail, which isolation guarantee is relevant, and whether the selected mechanism protects one row or a wider predicate. An annotation's presence is not enough to prove interception, enlistment, or commit.

Distinguish savepoint rollback from a separate transaction, flush from commit, and local database atomicity from cross-system reliability. For JDBC questions, inspect auto-commit and ownership. For pool questions, account for every replica and nested transaction. For outbox questions, identify the relay's duplicate-delivery window and consumer policy.

Reject absolute claims that higher isolation eliminates the need for retries, that prepared statements parameterize table names, or that a larger pool always improves throughput. A strong answer specifies both the guarantee and the cost, including contention, latency, recovery, and the application rule being protected.

## Cheatsheet

| Concern | Key distinction |
| --- | --- |
| Auto-commit | Statement completion commits according to JDBC rules |
| Local transaction | One owned connection boundary |
| Managed transaction | Let the manager control commit and rollback |
| Savepoint | Partial rollback, not independently committed work |
| Flush | Sends pending ORM work; not durable commit |
| Isolation | Database-specific concurrent-history guarantees |
| Optimistic version | Detect conflicting updates; retry business decision |
| Deadlock | Inspect cycle, consistent ordering, bounded whole-transaction retry |
| PreparedStatement | Bind values, allowlist dynamic identifiers |
| Query plan | Inspect representative data and statistics |
| Pool | Shared capacity budget across replicas |
| XA | Coordinated enlisted resources with recovery obligations |
| Outbox | Atomic local intent, relay may publish duplicates |

## Check yourself

### 1. Flush result

Does a successful ORM flush prove an order is committed?

**Answer:** No. It synchronizes pending work with the database inside the transaction. Commit can still fail, and the transaction can still roll back.

### 2. Pool closure

Why close a connection borrowed from a pool?

**Answer:** Closing returns the logical connection to its owner according to the pool contract. Failing to close leaks usable capacity even when the physical connection remains open.

### 3. Dynamic table

Can a question-mark parameter safely select an arbitrary table name?

**Answer:** No. Parameters bind values. Dynamic identifiers require a controlled construction strategy such as mapping allowed user choices to fixed identifiers.

### 4. Advanced: stable snapshot

Does Repeatable Read universally prevent every cross-row invariant violation?

**Answer:** No. Guarantees vary by database, and snapshot-based implementations can permit write skew. Analyze the invariant and use suitable coordination, constraints, or serializable execution.

### 5. Advanced: unknown commit

A connection fails during commit. Should the application immediately repeat the payment?

**Answer:** Not without resolving or safely tolerating the uncertain outcome. Use a stable idempotency/business key and reconciliation; the original commit may have succeeded.

### 6. Advanced: outbox duplicate

Why can a consumer still receive the same outbox event twice?

**Answer:** The relay may publish successfully and crash before recording that fact. Replaying the pending row republishes the event, so consumers need idempotency or deduplication.

## Sources

Reviewed 2026-09-25. Baselines: JDBC in Java 17, Jakarta Transactions 2.0, PostgreSQL 17 where database-specific behavior is named.

- [JDBC Connection](https://docs.oracle.com/en/java/javase/17/docs/api/java.sql/java/sql/Connection.html)
- [PreparedStatement](https://docs.oracle.com/en/java/javase/17/docs/api/java.sql/java/sql/PreparedStatement.html)
- [Jakarta Transactions](https://jakarta.ee/specifications/transactions/2.0/jakarta-transactions-spec-2.0.html)
- [PostgreSQL isolation](https://www.postgresql.org/docs/17/transaction-iso.html)
- [PostgreSQL explicit locking](https://www.postgresql.org/docs/17/explicit-locking.html)
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html)
- [PostgreSQL constraints](https://www.postgresql.org/docs/17/ddl-constraints.html)
- [Debezium outbox event router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)
