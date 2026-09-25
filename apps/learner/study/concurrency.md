## Understand

Concurrency is about interleavings and ownership. A data race occurs when threads access shared mutable state without the required coordination and at least one access writes. Prefer immutable values, confinement or a clear synchronization policy.

`synchronized` provides mutual exclusion and visibility across the same monitor. `volatile` provides visibility/order guarantees for the variable but does not make `count++` atomic. Atomic classes support individual atomic updates; invariants spanning multiple fields may still require a lock or a redesigned state representation.

Executors manage task execution. A large or unbounded task queue can hide overload until memory or latency becomes unacceptable. A larger thread pool cannot increase a database connection pool's capacity. Limit concurrency at the scarce resource and define rejection, timeout and cancellation behavior.

## Apply

A worker blocks in `queue.take()`. Shutdown interrupts it. If the worker cannot propagate `InterruptedException` and must stop, restore interruption and leave its work loop:

```java
try {
    Work item = queue.take();
    process(item);
} catch (InterruptedException interrupted) {
    Thread.currentThread().interrupt();
    return;
}
```

This fragment belongs in the worker operation. Swallowing the exception and continuing can prevent shutdown. Restoring the flag without leaving a blocking retry loop may cause repeated immediate interruptions.

For a suspected deadlock, inspect a thread dump and identify who owns and waits for each monitor. A consistent lock acquisition order prevents a circular wait. A heap dump answers different questions about retained objects.

## Cheatsheet

| Tool | Use carefully |
| --- | --- |
| `Future.get` | Waits; use timeout where bounded latency matters |
| `CompletableFuture` | Compose results; know which executor runs each stage |
| `ConcurrentHashMap` | Prefer atomic operations such as `compute` over get-then-put races |
| Thread-local values | Reused pool threads need cleanup; not a universal context propagation mechanism |
| Jakarta managed executor | Container-supported execution and context, rather than ad hoc threads |
| Virtual threads | Java 21 blocking-I/O concurrency; still bound connections and memory |

## Check yourself

Why can two threads lose an increment on a volatile integer?

**Answer:** Increment comprises a read, addition and write. Both can read the same value and then write the same result. Use a suitable atomic operation or lock for the complete update.

## Sources

[Concurrency basics](https://docs.oracle.com/javase/tutorial/essential/concurrency/) · [Concurrent utilities](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/package-summary.html) · [Jakarta Concurrency](https://jakarta.ee/specifications/concurrency/3.1/)
