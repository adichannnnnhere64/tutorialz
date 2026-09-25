## Understand

### Learn features with their release boundaries

This chapter uses Java 17 as its language foundation and Java 21 for explicitly marked additions. Records and instanceof patterns became final in Java 16; sealed classes became final in Java 17. Record patterns, pattern matching for switch, virtual threads, and sequenced collections became final in Java 21. A framework's minimum supported JDK is a separate compatibility question. A feature shown in current documentation may not exist in the release used by an exam or production service.

Preview features require explicit enabling and are tied to their release. Do not treat a preview syntax from one JDK as a stable source contract on another. None of this chapter's complete programs requires preview flags. The point of newer language features is to make data and control flow clearer, not to compress every operation into the shortest possible expression.

### Records model transparent data

A record declares components and supplies corresponding accessors, a canonical constructor, equality, hashing, and a string representation. It is implicitly final and cannot declare arbitrary extra instance fields. It can implement interfaces, declare static members, and define additional behavior. Component accessors use the component name, not a JavaBeans get prefix, so framework support needs verification.

Record immutability is shallow. A final component reference can still point to a mutable list, array, or object. A compact constructor can validate and normalize constructor parameters before the compiler assigns component fields. Defensive copying must match the element type and exposure policy. Arrays are especially subtle: generated record equality treats array components through their ordinary equality behavior, not automatic deep element comparison.

### Closed alternatives and patterns

Sealed types restrict permitted direct subtypes. A permitted subtype must continue or end that restriction with sealed, non-sealed, or final as appropriate; records are implicitly final. In a named module, permitted direct subtypes belong to the same module; in the unnamed-module case they belong to the same package. A non-sealed branch deliberately reopens extension, so the entire hierarchy is not necessarily a fixed set of leaf classes.

Patterns combine a type test with binding or decomposition. The compiler tracks where a pattern variable is definitely available. A successful instanceof test on the left of && allows the variable on the right. A failed test followed by an early return can also establish scope later. This is control-flow reasoning, not simply placing the variable everywhere after its textual declaration.

## Apply

### Example M1: Defensively copy a record component

Complete Java 17 program; expected output: `1`.

```java
import java.util.*;
record Basket(List<String> items) {
  Basket { items = List.copyOf(items); }
}
class Main {
  public static void main(String[] args) {
    List<String> source = new ArrayList<>();
    source.add("book");
    Basket basket = new Basket(source);
    source.add("pen");
    System.out.print(basket.items().size());
  }
}
```

The constructor snapshots the list structure, so later additions to the source do not change the basket. Strings are immutable, making the element references safe for this example. Replacing strings with mutable Line objects would require a separate element policy. List.copyOf rejects null elements; that is a validation choice, not an invisible implementation detail.

### Example M2: Exhaustive domain alternatives

Complete Java 21 program; expected output: `paid:12`.

```java
sealed interface Result permits Paid, Declined {}
record Paid(int amount) implements Result {}
record Declined(String reason) implements Result {}
class Main {
  static String describe(Result result) {
    return switch (result) {
      case Paid(int amount) -> "paid:" + amount;
      case Declined(String reason) -> "declined:" + reason;
    };
  }
  public static void main(String[] args) {
    System.out.print(describe(new Paid(12)));
  }
}
```

The switch covers the permitted alternatives and record patterns extract their data. This exact switch is Java 21, not ordinary non-preview Java 17. A null input is not handled by these cases; define a null contract or add case null where appropriate. Exhaustiveness over known subtypes does not imply every possible reference value is acceptable.

### Example M3: Reversed views remain connected

Complete Java 21 program; expected output: `D,C,B,A`.

```java
import java.util.*;
class Main {
  public static void main(String[] args) {
    List<String> values = new ArrayList<>(List.of("A", "B", "C"));
    List<String> reversed = values.reversed();
    values.addLast("D");
    System.out.print(String.join(",", reversed));
  }
}
```

The reversed list is a view, not an independent snapshot. Mutation of the original is reflected in it. Whether particular mutation operations are supported depends on the backing collection; reversing an unmodifiable collection does not grant permission to modify it. Use an explicit copy if the requirement is a historical snapshot rather than alternate traversal.

### Example M4: Own the virtual-thread executor

Complete Java 21 program; expected output: `true`.

```java
import java.util.concurrent.*;
class Main {
  public static void main(String[] args) throws Exception {
    try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
      Future<Boolean> result = executor.submit(() -> Thread.currentThread().isVirtual());
      System.out.print(result.get());
    }
  }
}
```

Each submitted task gets a virtual thread. The executor is owned by a try-with-resources scope and closes after the work completes. This example demonstrates thread kind and lifetime, not a performance benchmark. A virtual thread blocked on a database connection still consumes a pending request and may retain application data, even when it is inexpensive compared with a platform thread.

## Advanced

### Record invariants and API evolution

Validate invariants in the canonical construction path so every caller receives the same checks. Additional constructors must delegate appropriately. Normalization should preserve a clear value meaning: trimming an identifier may be reasonable, silently rounding a monetary amount may not be. An accessor that exposes a mutable array can undo constructor-side copying; copy on exposure as well when the contract requires isolation.

Changing record components changes construction, accessors, equality, and often serialization shape. This makes records useful for deliberately transparent values, but not automatically suitable for long-lived public APIs whose representation must remain hidden. ORM entity models may require no-argument construction, proxying, or mutable identity behavior that ordinary records do not provide. Use records for projections and transport values where supported; check provider versions instead of assuming all data objects should become records.

### Pattern dominance and exhaustiveness

Place more specific patterns before broader patterns where the language requires it. An unguarded broad type pattern can dominate a later narrower one, making that case unreachable and a compilation error. Guards refine matching, but a guarded case generally does not cover all values of its type. Null handling must be explicit where null is permitted; default is not a universal replacement for case null.

A switch expression must produce a value or complete abruptly on every applicable path. Arrow cases do not fall through like traditional colon labels. A block case uses yield to produce its value. Sealed hierarchies help compilers assess coverage, but separately compiled evolution can still create runtime mismatches if producer and consumer versions disagree. Compatibility testing matters even when each artifact compiled successfully in isolation.

### Sequenced collection semantics

SequencedCollection supplies a uniform vocabulary for first, last, and reverse encounter order. SequencedSet adds uniqueness with a defined encounter order; SequencedMap provides corresponding ordered-map operations. These abstractions do not impose one storage strategy or complexity guarantee. A list supports indexed access, while a sequenced collection need not. Empty first/last access and unsupported insertion operations must be handled according to each API.

A reversed view changes traversal direction, not the meaning of element equality. LinkedHashMap encounter order and sorted-map comparator order are different contracts. A sorted structure cannot generally accept arbitrary positioning merely because the sequenced API names first and last. Review supported operations instead of assuming every implementation supports every optional mutation. Backed views remain subject to the original collection's concurrency and invalidation rules.

### Virtual threads and pinning boundaries

Virtual threads are intended for large numbers of tasks that spend time waiting, particularly on supported blocking I/O. They do not add processors or make a CPU-intensive loop run faster. Do not pool virtual threads merely to imitate a scarce platform-thread pool; limit access to scarce dependencies with a separate admission mechanism such as a semaphore or connection pool.

In Java 21, blocking while inside synchronized code can pin a virtual thread to its carrier. Native or foreign interactions can also affect unmounting. Diagnose actual pinning and contention before rewriting locks indiscriminately. Later JDK releases changed synchronized pinning behavior, so operational guidance must state the JDK version. ThreadLocal-heavy designs also deserve review because per-thread data multiplied across many virtual threads may consume substantial memory.

## Production

### Introduce features at explicit boundaries

Adopt records first where value semantics are already intended, such as immutable command inputs or query projections. Test JSON binding, validation, persistence integration, and equality-sensitive collections. A generated toString can expose component data in logs; do not put credentials or sensitive payloads into routinely logged records without a deliberate redaction strategy.

Use sealed alternatives for domains where the owning module controls the choices, such as a payment outcome or parser result. Avoid sealing extension points that third-party implementations are expected to implement. For error outcomes, distinguish invalid input, temporary dependency failure, and permanent business rejection instead of forcing every failure into one boolean. Patterns make that distinction easier to consume, but do not replace thoughtful domain modeling.

### Measure concurrency changes

Before enabling virtual-thread request execution, record baseline throughput, latency percentiles, memory, database wait time, and downstream errors. Load-test beyond the sustainable rate to verify rejection and timeouts rather than only steady-state success. More admitted requests can make a database slower and cause a timeout cascade even when the Java thread scheduler performs well.

Keep request context propagation and cleanup explicit. Virtual threads do not turn an unbounded cache into a bounded one or provide automatic business cancellation. An executor closing waits for its work according to its contract; it is not a substitute for deadlines inside each task. Shutdown tests should include stuck I/O, interrupted tasks, partial external effects, and resources that require explicit closure.

## Exam reasoning

### State the version before evaluating syntax

A Java 17 question can use records, sealed types, and instanceof patterns without preview, but not the finalized Java 21 pattern switch used above. A code fragment can be logically sound yet fail to compile under the declared release. Separate that compilation question from runtime behavior and from whether the design is appropriate.

For record questions, inspect component mutability, constructor normalization, and generated equality rather than assuming deep immutability. For sealed types, examine direct subtypes and module/package rules. For pattern questions, track scope, dominance, null, and exhaustive coverage. For reversed views, ask whether a copy was actually made.

Performance choices should name the bottleneck. Virtual threads fit many blocking workloads; parallel CPU computation still depends on processor capacity and algorithm design. A choice claiming unlimited concurrency or faster SQL merely from changing thread type should be rejected. The strongest answer connects a feature's exact guarantee to the stated requirement.

## Cheatsheet

| Feature | Release and limitation |
| --- | --- |
| Record | Final Java 16; shallowly immutable components |
| Compact constructor | Validate or normalize parameters before field assignment |
| instanceof pattern | Final Java 16; variable scope follows proven match |
| Sealed type | Final Java 17; controlled direct subtypes |
| non-sealed branch | Explicitly allows further unknown subtypes |
| Record patterns | Final Java 21; decompose matching record values |
| Pattern switch | Final Java 21; consider dominance, coverage, and null |
| Sequenced collections | Java 21; encounter order is explicit |
| reversed | Backed view, not automatically a snapshot |
| Virtual threads | Final Java 21; blocking scalability, not CPU acceleration |
| Java 21 pinning | Synchronized blocking can retain a carrier |
| Preview | Explicit flags and release-specific compatibility |

## Check yourself

### 1. Record list

Does a record containing ArrayList automatically prevent additions?

**Answer:** No. The component reference is final, but the list may remain mutable. Copy it appropriately and consider whether the elements are also mutable.

### 2. Pattern scope

Why is a bound String variable usable after instanceof on the left side of &&?

**Answer:** The right side executes only after a successful match. With ||, the right side can execute after failure, so the same guarantee does not hold.

### 3. Reversed snapshot

Does appending to the original ArrayList change its reversed view?

**Answer:** Yes. The view reflects the backing list. Make an explicit copy when an independent snapshot is required.

### 4. Advanced: sealed evolution

Does an exhaustive compiled switch remove the need to coordinate library upgrades?

**Answer:** No. Separately compiled producer and consumer versions can disagree about alternatives. Exhaustiveness is checked against the types known at compilation, not every future binary change.

### 5. Advanced: virtual-thread capacity

Can ten thousand virtual threads execute simultaneously through forty database connections?

**Answer:** No. Only available connections can perform the database work. Bound admission, measure acquisition waits, and use end-to-end deadlines rather than treating cheap threads as unlimited capacity.

### 6. Advanced: array equality

Do two records with separately allocated equal-content array components automatically compare equal?

**Answer:** No. Generated equality does not invent deep array equality. Choose a value-oriented representation or deliberately implement the required equality and defensive-copy contracts.

## Sources

Reviewed 2026-09-25. Baselines: Java 17 and explicitly labeled Java 21. No preview features are required by the complete programs.

- [Records](https://dev.java/learn/records/)
- [Sealed classes](https://docs.oracle.com/en/java/javase/21/language/sealed-classes-and-interfaces.html)
- [Java 21 pattern switch](https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html)
- [Java 21 record patterns](https://docs.oracle.com/en/java/javase/21/language/record-patterns.html)
- [SequencedCollection](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/SequencedCollection.html)
- [SequencedMap](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/SequencedMap.html)
- [Java 21 virtual threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
- [ExecutorService lifecycle](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ExecutorService.html)
