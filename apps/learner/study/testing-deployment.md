## Understand

Good tests verify observable behavior at the boundary that can fail. Unit tests isolate business rules. Integration tests verify wiring, persistence, transactions and external protocols. Contract tests check provider/consumer expectations. End-to-end tests cover a small number of critical user journeys.

Mocking a repository does not test SQL, transaction rollback or a real unique constraint. A test transaction that always rolls back may miss failures raised only at commit. Exercise successful commit, expected rollback, concurrent conflicts and retry behavior against representative infrastructure.

Maven and Gradle describe dependency and build graphs. Use pinned compatible versions, reproducible wrappers/toolchains and the project's test commands. `javac --release` restricts standard API availability for an older Java target; a lower class-file target alone is insufficient.

## Apply

For a tenant-aware invoice cache, create two tenants with the same invoice ID and different amounts. Call the service for A, then B, against the same cache. Assert B receives B's amount. Clearing the cache between calls would conceal the collision instead of exercising it.

For production diagnosis, begin with the failure signal and timeline. Correlate logs, request latency, error rates, queue lag and connection-pool wait time. Change one relevant constraint and measure again; increasing every pool size can move the bottleneck or overload the database.

## Cheatsheet

| Tool / practice | Answers |
| --- | --- |
| `jcmd PID Thread.print` | Which threads block or form a monitor cycle? |
| JFR / profiler | Where is time or allocation spent under representative load? |
| `jdeps --jdk-internals` | Which compiled dependencies use internal JDK APIs? |
| `jdeprscan` | Which referenced APIs are deprecated? |
| `javap` | What members/bytecode are in this class? |
| Health/readiness | Is the process alive / should it receive new traffic? |
| Database migrations | Versioned schema changes with compatibility and recovery planning |
| Graceful shutdown | Stop intake, drain bounded in-flight work, then release resources |

## Check yourself

An application responds slowly while most threads wait for database connections. Should you immediately double its worker threads?

**Answer:** No. Inspect connection hold times, query latency, transaction scope and database capacity first. More waiting workers do not increase available connections and can increase memory and scheduling pressure.

## Sources

[JUnit guide](https://docs.junit.org/current/user-guide/) · [Maven introduction](https://maven.apache.org/guides/getting-started/) · [javac reference](https://docs.oracle.com/en/java/javase/17/docs/specs/man/javac.html) · [jcmd reference](https://docs.oracle.com/en/java/javase/17/docs/specs/man/jcmd.html)
