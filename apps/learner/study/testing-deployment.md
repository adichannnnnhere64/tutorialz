## Understand

### Test a claim at the right boundary

A unit test isolates a small piece of logic. An integration test exercises a real boundary such as database mapping, transaction behavior, HTTP binding, or broker delivery. A contract test checks compatibility between consumers and providers. An end-to-end test follows a user-visible path through assembled components. These categories describe purpose, not a competition where one replaces every other.

A mock can prove how code reacts to a collaborator's programmed response. It cannot prove the real collaborator behaves that way. Mocking a repository to throw a constraint exception does not validate the migration, SQL, driver, or actual commit timing. Conversely, starting a whole server to test a pure arithmetic rule adds cost without necessarily adding confidence. Choose the smallest test that can falsify the specific claim.

This chapter uses Java 17/21 diagnostics and JUnit Jupiter 5.11 as concrete reference points. Framework and container versions should be pinned for reproducibility. The practices also apply to Jakarta applications tested in a matching server and Spring applications tested with appropriate slices and full contexts.

### Determinism makes failures useful

Control time, randomness, locale, time zone, external services, and mutable global state when they affect a test. Inject Clock for time-based rules and seed generated cases when repeatability matters. Avoid arbitrary sleeps as a synchronization mechanism. Await an observable condition with a deadline and a useful failure message, or coordinate threads with explicit latches/barriers in concurrency tests.

Tests should own and clean up their resources. Parallel execution can expose hidden shared ports, static state, reused schemas, or files with fixed names. Isolation is not only a performance issue: order-dependent tests can conceal real defects and waste incident time. A passing rerun does not explain a flaky failure; collect evidence and fix the nondeterministic assumption.

### A release is an artifact plus an environment

Reproducible builds aim to produce equivalent artifacts from the same inputs, controlling toolchains, dependency versions, plugins, timestamps, and packaging. A lockfile or dependency BOM is useful but does not pin every build input automatically. Record artifact digests and promote the same tested artifact across environments rather than rebuilding a different one for production.

Deployment also includes configuration, secrets, database migration, message compatibility, health signals, and rollback or roll-forward strategy. A green compiler does not validate those operational contracts. Define what success looks like after deployment and which signals trigger intervention. Version labels without immutable artifact identity are insufficient for precise diagnosis.

## Apply

### Example TEST1: Freeze the business clock

Complete Java 17 program; expected output: `2026-09-25`.

```java
import java.time.*;
class Main {
  static LocalDate businessDate(Clock clock) {
    return LocalDate.now(clock);
  }
  public static void main(String[] args) {
    Clock fixed = Clock.fixed(Instant.parse("2026-09-25T12:00:00Z"), ZoneOffset.UTC);
    System.out.print(businessDate(fixed));
  }
}
```

The result does not depend on the machine's current day or default zone. A real business-date rule may use a specific regional zone and cutoff time, so test those deliberately. Freezing the clock does not remove the need for daylight-saving and leap-day cases; it makes those cases reproducible instead of dependent on when CI happens to run.

### Example TEST2: Reach commit in an integration test

A service inserts two rows that violate a deferred database constraint. A test wrapped in a transaction calls the service, checks in-memory values, and then rolls back automatically. It can pass without ever observing the commit-time failure.

Create a test that allows the application transaction to complete and assert the actual outcome from a separate read boundary. Use a representative database version and migration. Flush can expose some SQL and immediate constraints, but is not a substitute for commit when the rule is deferred. Keep test cleanup separate so it does not accidentally hide the failure being tested.

### Example TEST3: Diagnose blocked work

Illustrative diagnostic commands; replace 12345 with a verified JVM process ID. These commands are for an authorized environment, and diagnostic artifacts may contain sensitive data.

```text
jcmd 12345 Thread.print -l
jcmd 12345 JFR.start name=latency settings=profile duration=60s filename=latency.jfr
```

Repeated thread snapshots can show lock cycles, pool waits, and stuck calls. A bounded JFR recording can connect execution, allocation, and waiting events. Choose event settings and duration according to overhead and privacy requirements. Neither command repairs the application; preserve the evidence and correlate it with request and dependency metrics.

### Example TEST4: Expand before contracting a schema

A release needs to rename a customer field. First add a compatible new column or representation while old code still works. Deploy code that can populate and read the transition safely, backfill existing data, verify consistency, then remove the old path only after all old consumers are gone.

The exact dual-write or read-fallback strategy must avoid divergence and define a source of truth. A destructive rename in the first migration can break old replicas during a rolling deployment. Rolling application binaries back is not enough if the database schema has already removed what they need.

## Advanced

### Transactional tests and thread boundaries

Framework-managed test transactions are often bound to the test thread. Code running through an actual HTTP server, asynchronous executor, or preemptive timeout may execute on another thread and use a different transaction. It may commit data that the test's rollback does not clean up. Understand the test harness rather than assuming an annotation surrounds every operation indirectly triggered by the test.

Use separate assertions for mapping, flush, commit, and post-commit visibility when they are distinct risks. Test uniqueness races with two real transactions instead of sequential calls through one persistence context. Verify optimistic-lock failures and retry policies with fresh state. A persistence context cache can otherwise make a test appear to read the database while it only reads managed objects.

### Contract and failure-path coverage

A contract includes field meaning, units, enum evolution, requiredness, status codes, headers, and failure behavior. A JSON schema catches shape violations but not every semantic incompatibility. Consumer-driven contract tests can reveal assumptions, while provider integration tests verify actual behavior. Keep examples representative rather than approving every new provider response automatically.

For messaging, test duplicates, redelivery, poison messages, delayed delivery, ordering assumptions, and schema evolution. For HTTP, test uncertain outcomes, retries, rate limits, and cancellation. Inject failure at meaningful boundaries: before commit, after commit before response, after publish before acknowledgement. A random process kill is less informative unless the test records what durable state should remain.

### Containers and realistic dependencies

Testcontainers can provide disposable real services for integration tests, but image versions, initialization, readiness, network behavior, and cleanup still matter. Wait for the service condition the application needs, not merely an open TCP port. An empty database becoming reachable does not prove migrations finished or credentials work.

Reusable containers are an opt-in convenience with isolation caveats and are not a blanket CI strategy. Tests must not depend on leftover data from a prior run. Use unique schemas or controlled resets appropriate to the service, and inspect failure artifacts when startup fails. Pin images or digests according to the project's reproducibility policy and keep them patched through deliberate updates.

### JFR, thread dumps, heap dumps, and GC

A thread dump explains thread states and stack locations at a moment. Repeated samples help distinguish a transient wait from persistent blockage. A heap dump explains retained objects and reference paths, often at substantial size and operational cost. JFR provides time-correlated events with configurable overhead. Choose the tool based on the question rather than collecting the largest artifact first.

High heap usage is not automatically a leak; a leak involves unintended retention over time. Allocation pressure, retained size, native memory, direct buffers, and thread stacks are different categories. Garbage-collection pause data helps explain latency but does not prove every slow request is a GC problem. Correlate timestamps and compare live-set behavior across comparable workload phases.

## Production

### Health signals and controlled rollout

Liveness asks whether restarting the process is useful. Readiness asks whether the instance should receive traffic. Startup probes allow initialization time without premature liveness failure. A shared dependency outage should not automatically make every instance enter a restart loop. Design probes with bounded work and clear operational meaning.

Deploy gradually when appropriate, compare error rate and latency against a baseline, and keep a fast way to stop the rollout. Canary traffic must represent important user paths; a health endpoint alone does not exercise database writes or broker processing. Graceful shutdown should stop new work, drain in-flight operations, and fit the platform termination budget.

### Build provenance and recovery

Pin build plugins and toolchains as well as libraries. Record source revision, dependency inventory, artifact checksum, and relevant build configuration. Avoid embedding secrets or machine-specific paths. Verify signatures and integrity where the distribution workflow requires them. A reproducible unsigned archive and a timestamped signed artifact may have different reproducibility properties; describe what is actually checked.

Plan database backup and restore, broker recovery, transaction logs, and external reconciliation. A rollback button cannot undo a payment already sent or restore a dropped column without a recovery path. Prefer backward-compatible changes and explicit irreversible-step approval. Practice restore procedures in an authorized environment; an untested backup is only an assumption about recoverability.

### Make test failures actionable

A useful failure reports expected behavior, observed behavior, stable identifiers, and safe diagnostic context. Keep logs bounded and redact secrets. Retain screenshots or traces for UI failures, SQL plans for relevant performance tests, and container logs for startup failures. Do not mask a flaky test by unlimited retries or broadly increasing timeouts.

Track test suite duration and failure categories so confidence remains affordable. Fast checks should run frequently, while expensive environment and resilience tests can have explicit schedules and release gates. Every gate should map to a risk. A large numeric coverage percentage is not a substitute for testing authorization denial, commit-time integrity, or upgrade compatibility.

## Exam reasoning

### Ask what the test actually proves

A unit test with mocks proves local behavior under assumed responses. A controller slice proves selected web wiring. A database integration test proves behavior against its configured database and transaction boundary. An end-to-end test proves the exercised path, not every path. Select the missing test based on the unverified claim rather than choosing the largest-sounding test category.

For diagnostics, match symptom to evidence: lock contention suggests thread/lock data, retention suggests heap analysis, time-correlated latency suggests JFR and metrics, slow SQL suggests plans and database waits. For deployment, identify overlapping versions, state migration, health semantics, and irreversible side effects.

Reject shortcuts such as “rollback tests prove commit,” “sleep fixes async tests,” or “liveness should fail whenever any dependency fails.” Strong answers explain isolation, timing, ownership, and recovery. Tests and operations are part of the same reliability argument: the system must behave predictably both during normal use and during change.

## Cheatsheet

| Need | Evidence or technique |
| --- | --- |
| Pure rule | Fast unit test with explicit dependencies |
| HTTP binding | Slice or server integration test |
| Database integrity | Real schema, transaction, and commit boundary |
| Consumer compatibility | Contract plus provider behavior tests |
| Time-dependent rule | Inject Clock and test explicit zones/cutoffs |
| Async completion | Observable condition with bounded deadline |
| Real dependencies | Pinned disposable services and readiness checks |
| Lock diagnosis | Repeated thread dumps |
| Retained memory | Heap analysis with privacy and overhead controls |
| Correlated runtime events | Bounded JFR recording |
| Reproducible build | Pin toolchain, dependencies, plugins, packaging inputs |
| Health | Separate startup, readiness, and liveness |
| Schema migration | Expand, transition, verify, then contract |
| Release recovery | Artifact identity plus state/reconciliation plan |

## Check yourself

### 1. Mocked database

Does a mocked repository prove production SQL is valid?

**Answer:** No. It proves behavior against the programmed mock. Validate mapping and SQL against a representative real database.

### 2. Fixed sleep

Why is a two-second sleep a weak async test strategy?

**Answer:** It guesses timing instead of observing completion. Slow environments can fail and fast ones waste time. Await the actual condition with a bounded deadline.

### 3. Diagnostic choice

Which artifact is most directly useful for finding a monitor deadlock?

**Answer:** Thread/lock information, often through repeated thread dumps. A heap dump answers a different question about retained objects.

### 4. Advanced: rollback-only test

Why can a transactionally rolled-back test miss a deferred constraint failure?

**Answer:** It may never reach commit, where the database evaluates that constraint. Add a test of actual commit and post-commit outcome.

### 5. Advanced: health cascade

Why can checking a shared database in liveness worsen an outage?

**Answer:** All instances may restart despite being locally healthy, adding disruption without repairing the database. Readiness and dependency policy should be designed separately.

### 6. Advanced: binary rollback

Why is restoring an old application artifact insufficient after dropping a required column?

**Answer:** The persistent state is no longer compatible. Recovery needs a schema/data plan, not only a binary rollback; use staged compatible migrations where possible.

## Sources

Reviewed 2026-09-25. Baselines: JUnit Jupiter 5.11, Java 17/21 diagnostics. Diagnostic commands are illustrative and require authorization on the target JVM.

- [JUnit 5.11 guide](https://docs.junit.org/5.11.0/user-guide/index.html)
- [Spring transactional test boundaries](https://docs.spring.io/spring-framework/reference/6.2/testing/testcontext-framework/tx.html)
- [Testcontainers lifecycle](https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/)
- [Reusable-container caveats](https://java.testcontainers.org/features/reuse/)
- [Java 21 jcmd](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html)
- [Maven reproducible builds](https://maven.apache.org/guides/mini/guide-reproducible-builds.html)
- [Kubernetes probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/17/backup.html)
