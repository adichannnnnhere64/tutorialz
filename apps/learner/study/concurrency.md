## Understand

### Ownership before threads

Concurrency allows activities to overlap; parallelism executes activities simultaneously. A program can have concurrency bugs on one processor because operations interleave. Begin by identifying state, who owns it, and which operations must appear indivisible. An immutable request passed to one worker is easier to reason about than a mutable request shared among a controller, background task, and cache. More threads do not create more database connections or CPU capacity.

A data race involves conflicting accesses, at least one a write, without the required happens-before ordering. Race conditions are broader: two individually thread-safe operations can still violate a business rule. Checking a concurrent map and then inserting is not automatically one atomic action. Similarly, two atomic account balances do not make a transfer between them atomic. Define the invariant, then choose synchronization that protects the whole invariant.

### Visibility, atomicity, and ordering

The Java Memory Model describes permitted observations, not simply when a processor flushes a cache. Unlocking a monitor happens-before a subsequent lock of that monitor. A volatile write happens-before subsequent reads of that variable. Starting a thread publishes earlier actions to it; successful completion of join makes its completed actions visible. These relationships compose transitively. Sleeping does not establish a publication relationship.

Volatile is useful for a cancellation flag or a safely published replacement reference. It does not make increment atomic: increment still reads, adds, and writes. Synchronized supplies both exclusion and visibility when every participant follows the same locking policy. Locking two different objects does not protect the same invariant. A final reference cannot be reassigned, but the referenced object may still need synchronization.

### Tasks and lifetimes

An executor separates submission from execution policy. A Future represents completion, failure, or cancellation; it is not a guarantee that a task has stopped doing external work. Every task needs an owner responsible for its result and lifetime. Prefer explicit deadlines, cancellation behavior, and bounded resource use over detached work that outlives its request without supervision. In Jakarta applications, use container-supported managed execution when its services and contexts are required.

## Apply

### Example T1: Publish a result with join

Complete Java 17 program; expected output: `42`.

```java
class Main {
  static int result;
  public static void main(String[] args) throws InterruptedException {
    Thread worker = new Thread(() -> result = 42);
    worker.start();
    worker.join();
    System.out.print(result);
  }
}
```

The successful join supplies the ordering needed for this read; result does not need to be volatile in this particular program. Removing join changes the reasoning: the main thread might read before the write, with no replacement synchronization. Adding an arbitrary sleep is not a valid repair. This example has one writer and one final read; it does not justify unsynchronized reads while the worker remains active.

### Example T2: Protect an increment

Complete Java 17 program; expected output: `2000`.

```java
import java.util.concurrent.atomic.AtomicInteger;
class Main {
  public static void main(String[] args) throws InterruptedException {
    AtomicInteger count = new AtomicInteger();
    Runnable work = () -> {
      for (int i = 0; i < 1000; i++) count.incrementAndGet();
    };
    Thread a = new Thread(work);
    Thread b = new Thread(work);
    a.start(); b.start();
    a.join(); b.join();
    System.out.print(count.get());
  }
}
```

Each increment has an indivisible update. The joins ensure both loops complete before printing. Replacing this with a volatile integer loses atomicity even though individual reads and writes have volatile semantics. An atomic update function may be retried internally, so do not send email or debit a remote account inside that function.

### Example T3: Compose a dependent operation

Complete Java 17 program; expected output: `invoice:7`.

```java
import java.util.concurrent.CompletableFuture;
class Main {
  static CompletableFuture<String> invoice(int id) {
    return CompletableFuture.completedFuture("invoice:" + id);
  }
  public static void main(String[] args) {
    String result = CompletableFuture.completedFuture(7)
        .thenCompose(Main::invoice).join();
    System.out.print(result);
  }
}
```

ThenCompose flattens the future returned by the next operation. ThenApply would produce a future containing another future here. Neither inherently starts a new thread. These stages already have completed inputs and may run synchronously. Select an explicit executor for expensive asynchronous stages rather than assuming every future uses an isolated worker pool.

## Advanced

### Safe publication and immutable snapshots

Publish fully constructed objects through a documented mechanism such as a volatile reference, synchronized handoff, concurrent collection, or task submission. Do not let this escape a constructor into callbacks or worker threads before initialization completes. Final-field initialization guarantees are useful but do not turn a mutable object graph into an immutable one. A snapshot needs defensive copies of mutable inputs and no exposed mutable internals.

For a configuration refresh, build a complete immutable configuration and atomically replace one reference. Readers then see an old or new valid configuration rather than a mixture of individually updated fields. If several values must agree, place them in that snapshot or protect them with one lock. A version number read independently from the data is not a snapshot unless the protocol detects and retries inconsistent observations.

### Locks, conditions, and progress

Use try/finally when explicitly acquiring a ReentrantLock. Condition waiting belongs in a loop that rechecks its predicate because wakeups can be spurious and another thread may consume the condition first. Object.wait releases the relevant monitor while waiting; Thread.sleep does not release a held monitor. A signal announces that a condition may have changed, not that the recipient now owns a reserved item.

Deadlock requires a cycle of resource dependencies; a consistent global lock order removes the circular-wait opportunity for those locks. Timeouts bound a wait but still require recovery. Livelock means participants remain active without useful progress, while starvation means one participant is repeatedly denied progress. Fairness options can affect throughput and scheduling but are not a substitute for capacity planning or a proof of application-level fairness.

### Executor queueing and cancellation

ThreadPoolExecutor first creates core workers, then queues tasks, then can grow beyond core size when queueing fails, up to maximum size. With an unbounded queue, maximum size usually does not provide the expected scaling. A bounded queue and rejection policy make overload explicit. Caller-runs can slow a submitter, but expensive work on a request or event-loop thread may violate its latency contract. Silently discarding business tasks is rarely acceptable.

Interruption is cooperative. If a method can propagate InterruptedException, let its caller decide. If it cannot and must terminate, restore the interrupt flag and exit cleanly. Restoring the flag while repeatedly retrying the same interruptible call may create a busy loop. Shutdown stops new submissions and allows queued tasks to run; shutdownNow attempts interruption and returns tasks not started. Neither can forcibly make arbitrary code obey cancellation.

### CompletableFuture failures and execution

Non-async continuations can run on a completing thread. Async methods without an explicit executor normally use the common pool, shared with other work. Avoid blocking all workers while waiting for tasks queued to those same workers. Handle transforms success or failure; exceptionally recovers failures; whenComplete observes an outcome and can itself fail. AllOf coordinates completion but does not directly collect typed results.

Timeout completion does not necessarily stop underlying I/O. CompletableFuture cancellation completes it exceptionally; its interrupt parameter does not control an underlying worker as many callers expect from FutureTask. Carry cancellation to the actual operation when supported, configure network deadlines, and release permits in finally blocks. A response timeout and confirmed rollback of a remote side effect are different events.

## Production

### Bound the scarce dependency

Suppose 500 requests call a database with 20 usable connections. Creating 500 platform threads cannot make all calls execute simultaneously. They occupy memory and wait while deadlines expire. Measure acquisition wait, active connections, query duration, and queue length before raising thread counts. A semaphore or bounded executor can limit admission, but define what rejection means and ensure permits are released on every failure path.

Carry an end-to-end deadline through nested calls rather than giving each stage a fresh full timeout. Three sequential calls with separate ten-second limits may consume thirty seconds despite a ten-second user contract. Include queue time in the budget. Retry only transient failures and operations whose effects can safely be repeated. Cancellation after submission may race with completion, so preserve an operation ID for reconciliation.

### Diagnose with evidence

Take repeated thread dumps to distinguish stable blockage from a transient snapshot. Look for lock cycles, exhausted pools, workers waiting for their own queued dependencies, and long external calls. CPU profiling answers where execution time goes; heap analysis answers what retains memory; JFR connects scheduling, allocation, and latency events. Not every WAITING thread is broken: idle workers wait by design.

Clean up ThreadLocal values in reused threads, especially tenant, security, and diagnostic contexts. A thread name is not a trustworthy request identity. Context propagation across async boundaries must be deliberate and tested. Java 21 virtual threads improve scalability for many blocking workloads but do not accelerate CPU-bound algorithms or remove connection limits. Version-specific pinning and library support require verification; do not apply later JDK improvements retroactively to Java 21.

## Exam reasoning

### Build the ordering proof

For an output question, list reads and writes, then draw only relationships justified by program order and actual synchronization. Do not infer a relationship from source-code proximity in different threads. Ask separately whether updates are indivisible, whether values are visible, and whether completion has been awaited. A volatile flag may publish earlier writes, but a counter increment needs a separate atomicity argument.

For a design question, identify the constraint before choosing a primitive. One mutable invariant suggests a shared lock or immutable atomic snapshot. Independent counter updates may fit an atomic class. A bounded producer-consumer relationship may fit a blocking queue. Dependent remote calls may fit completion-stage composition with deadlines. A choice that says thread-safe without specifying which operation or invariant is protected is incomplete reasoning.

Avoid deterministic predictions where the contract permits multiple interleavings. A program that sometimes prints the expected number has not demonstrated correctness. Tests expose races but generally cannot prove their absence. Prefer specified guarantees, and distinguish interruption requests from task termination and message delivery from business completion.

## Cheatsheet

| Need | Mechanism and boundary |
| --- | --- |
| Publish replacement | Volatile reference; construct the full value first |
| Compound invariant | Consistent lock or atomic immutable state transition |
| Independent increment | AtomicInteger, not separate get and set |
| Contended statistics | LongAdder; sum is not an atomic snapshot |
| Await completion | Future.get or Thread.join, with suitable deadline |
| Dependent future | thenCompose flattens; thenApply transforms |
| Independent results | thenCombine; define failure and cancellation |
| Backpressure | Bound queues and dependency concurrency |
| Stop cooperatively | Interrupt or cancellation protocol, cleanup, exit |
| Reused thread context | Explicit propagation and ThreadLocal removal |
| Jakarta execution | Managed executor with documented context guarantees |
| Virtual threads | Java 21; scarce resources still require limits |

## Check yourself

### 1. Volatile increment

Two workers each increment a volatile int 1,000 times. Must the result be 2,000 after joining?

**Answer:** No. Join provides completion and visibility, but increment can overwrite another increment. Use an atomic increment or a consistent lock around the complete update.

### 2. Waiting while locked

Does sleeping inside a synchronized block release its monitor?

**Answer:** No. Object.wait releases the monitor on which it waits and reacquires it before returning. Its condition must be checked in a loop.

### 3. Future shape

A callback returns CompletableFuture<Invoice>. Which operation avoids a nested future?

**Answer:** ThenCompose represents the eventual Invoice through one stage. ThenApply is appropriate when the callback returns the immediate transformed value.

### 4. Advanced: queue growth

A pool has core size four, maximum fifty, and an unbounded queue. Why are only four workers busy?

**Answer:** After core workers exist, tasks are queued. Additional workers are generally created only when queueing fails. Maximum size does not provide the intended overload control.

### 5. Advanced: cancellation and effects

A timed-out future represents a payment request. Does timeout prove payment did not happen?

**Answer:** No. Query by a stable operation ID and use idempotent retry or reconciliation. Separately attempt cancellation of underlying work where supported.

### 6. Advanced: immutable configuration

Why replace one volatile immutable configuration instead of four volatile settings?

**Answer:** Readers obtain one consistent version. Individual volatile fields provide visibility but do not make their combined update atomic, permitting mixed versions.

## Sources

Reviewed 2026-09-25. Baseline: Java 17 contracts; virtual threads are Java 21. Examples are original, not official assessment questions.

- [Memory model](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html)
- [Concurrent utilities](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/package-summary.html)
- [Executor queueing](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)
- [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
- [Condition](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/locks/Condition.html)
- [AtomicInteger](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html)
- [Virtual threads](https://openjdk.org/jeps/444)
- [Jakarta Concurrency](https://jakarta.ee/specifications/concurrency/3.1/)
