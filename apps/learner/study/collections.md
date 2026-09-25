## Understand

### Choose the contract before the implementation

This chapter targets Java 17, with later sequenced-collection APIs covered separately. You should understand equality, references, interfaces and generics first. The goal is to choose a collection whose ordering, uniqueness, mutation and concurrency contracts match the use case, then explain the costs and failure modes of that choice.

A List preserves positional sequence and can contain duplicates. A Set represents uniqueness according to its contract. A Map associates keys with values. A Queue or Deque expresses insertion/removal behavior rather than arbitrary indexed access. The interface is the starting point; null support, iteration order, synchronization and optional mutation operations differ among implementations.

### Ordering, uniqueness and equality

Hash-based collections depend on compatible equals and hashCode behavior. Sorted collections use their ordering relation to determine equivalence for membership. A comparator that returns zero for different values can intentionally or accidentally collapse them in a TreeSet or as TreeMap keys.

Do not assume that a HashMap's observed iteration order is an API guarantee. If predictable encounter order is required, choose an implementation with the relevant contract. Likewise, an immutable-looking factory result should not be assumed to have a particular concrete implementation class or a modifiable backing structure.

### Generic invariance and PECS

List<Integer> is not a subtype of List<Number>. If it were, code could insert a Double through a Number-typed view into a list intended to contain only Integer values. Wildcards express constrained access without making that unsafe relationship legal.

PECS means producer extends, consumer super. Read Number values from a List<? extends Number>; add Integer values to a List<? super Integer>. A wildcard does not change the runtime elements or convert values. It changes what operations the compiler can safely permit through that reference.

## Apply

### Example G1: copy from a producer into a consumer

Complete Java 17 program; expected output: `[1, 2]`.

```java
import java.util.*;
class Main {
  static <T> void copy(List<? extends T> source, List<? super T> target) {
    for (T item : source) target.add(item);
  }
  public static void main(String[] args) {
    List<Integer> source = List.of(1, 2);
    List<Number> target = new ArrayList<>();
    copy(source, target);
    System.out.print(target);
  }
}
```

The source produces values compatible with T and the target accepts them. The generic method does not claim that Integer and Number lists are interchangeable for every operation. It exposes only the capabilities needed by this copy operation.

### Example G2: comparator equivalence changes set membership

Complete Java 17 program; expected output: `2:true`.

```java
import java.util.*;
class Main {
  public static void main(String[] args) {
    Set<String> words = new TreeSet<>(Comparator.comparingInt(String::length));
    words.add("cat");
    words.add("dog");
    words.add("lion");
    System.out.print(words.size() + ":" + words.contains("sun"));
  }
}
```

The comparator treats all three-letter strings as equivalent. Therefore dog does not create a new member after cat, and contains for sun finds an ordering-equivalent member. If distinct strings must remain distinct, add an appropriate tie-breaker, such as natural ordering. An inconsistent-with-equals comparator can make a sorted set behave unexpectedly in contexts relying on the general Set contract.

### Example G3: view versus snapshot

Complete Java 17 program; expected output: `2:1`.

```java
import java.util.*;
class Main {
  public static void main(String[] args) {
    List<String> original = new ArrayList<>(List.of("a"));
    List<String> view = Collections.unmodifiableList(original);
    List<String> snapshot = List.copyOf(original);
    original.add("b");
    System.out.print(view.size() + ":" + snapshot.size());
  }
}
```

The view reflects backing-list changes while preventing mutation through its own API. The copy captures the list's elements at creation. Neither operation deep-copies arbitrary mutable elements. Choose the ownership semantics explicitly when returning collections from services or value objects.

### Example G4: atomic map update

Complete Java 17 program; expected output: `2`.

```java
import java.util.concurrent.*;
class Main {
  public static void main(String[] args) {
    ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
    counts.merge("paid", 1, Integer::sum);
    counts.merge("paid", 1, Integer::sum);
    System.out.print(counts.get("paid"));
  }
}
```

The map operation combines update logic under its documented concurrency contract. A separate get followed by put would be a different compound operation and could lose updates under concurrency. Keep mapping functions short and respect restrictions on recursive updates; do not turn an atomic map callback into a long network transaction.

## Advanced

### Erasure and heap pollution

Generics primarily enforce compile-time relationships, while many type parameters are erased in runtime representation. Raw types, unchecked casts and unsafe varargs operations can create heap pollution: a reference promises one parameterized type while its actual contents violate that promise.

A ClassCastException can then occur far from the unsafe insertion when the compiler-generated cast checks a retrieved value. Treat unchecked warnings as evidence to investigate, not background noise to suppress globally. When an unavoidable boundary requires an unchecked cast, isolate it, validate the assumption and document why the rest of the API remains safe.

### Wildcard capture and API shape

A List<?> can safely produce Object values, but it cannot accept an arbitrary non-null Object because its element type is unknown. A helper generic method can capture that unknown type and perform operations that preserve it. This is different from replacing the wildcard with Object, which makes a stronger and usually incorrect insertion promise.

Avoid returning unnecessarily complex wildcard types from public APIs when a simpler type parameter communicates the relationship. Wildcards are useful for flexible inputs, but readers still need to understand the capability being promised. Do not apply PECS mechanically to every declaration without considering whether the method both reads and writes.

### Mutable keys and equality stability

If a key's equality-significant state changes while it is stored in a HashMap, lookup may no longer find it through the expected hash bucket. The entry has not necessarily disappeared from iteration; its indexing assumptions have been broken. Immutable key values are usually easier to reason about.

An identity-based map intentionally uses reference identity rather than ordinary equals semantics. That can be useful for object-graph bookkeeping but is usually wrong for business identifiers such as account numbers. Select identity semantics consciously and explain them to callers.

### Views, fixed-size lists and mutation support

Arrays.asList creates a fixed-size list backed by the array. Replacing an element is different from structurally adding or removing one. SubList is also a view, with restrictions around structural changes to the backing list outside the view. An unmodifiable wrapper, a fixed-size view and an independent immutable snapshot are distinct contracts.

Factory methods such as List.of reject null elements and do not support mutation. They do not make mutable elements themselves immutable. Before storing a collection returned by another component, determine whether its owner can still change its contents or invalidate a view.

### Iteration and concurrent modification

Fail-fast iterators can detect some unexpected structural modifications, but they are not a synchronization mechanism or a reliable basis for correctness under data races. Do not write code that depends on ConcurrentModificationException always arriving before damage is done.

Concurrent collections have their own iteration contracts, such as weakly consistent traversal or snapshot-style iteration. CopyOnWriteArrayList favors read-heavy situations with relatively infrequent writes because mutation copies underlying state. Its iterator does not represent every later update. Choose according to workload and consistency needs, not the presence of “concurrent” in a class name.

### Performance beyond big-O labels

ArrayList offers efficient indexed access and amortized append, while insertion in the middle moves elements. LinkedList has different structural costs, but reaching an index still requires traversal and individual nodes have allocation/locality overhead. “Linked lists make insertion constant time” omits how the insertion position was found.

Hash table performance depends on hashing, collisions, resizing and workload. Pre-sizing a known bulk operation can help avoid repeated growth, but excessive capacity wastes memory. Sorted structures pay for ordering and navigation. Measure realistic key sizes, iteration patterns and contention rather than choose solely from a one-line complexity chart.

## Production

### Diagnose a disappearing map entry

A team stores a mutable Customer object as a key, then changes the customer's email, which contributes to hashCode. A subsequent get returns no result even though iteration still shows the entry. Reproduce the mutation boundary and replace the key with an immutable identifier value. Copying the whole map after every update treats the symptom rather than correcting the identity model.

Include equality and hashing tests for custom keys. Verify equal values produce equal hashes, and document whether keys are immutable. Avoid persisting hash codes as durable identifiers: collisions are allowed and hash implementation details can change.

### Bound shared caches and aggregation

A thread-safe map can still grow without limit. Define entry lifetime, eviction, memory budget and ownership when using one as a cache. Atomic updates do not establish a complete cache policy, and a map's concurrency support does not automatically make each stored mutable value safe.

For counters under heavy contention, choose a value type and aggregation approach based on required read consistency. A highly scalable approximate snapshot is not interchangeable with an atomic balance invariant. The concurrency chapter explains why choosing an atomic primitive alone cannot enforce every multi-field business rule.

### Return deliberate collection contracts

A service returning a live mutable collection lets callers interfere with future operations. A service returning a large copy on every call can create avoidable allocation. Choose a snapshot, read-only view, paginated result or streaming API based on lifetime and size, and document the choice.

Validate null and duplicate behavior at integration boundaries. A migration from one collection factory to another can change whether nulls or duplicate keys are accepted. Tests should cover those cases rather than only the happy-path list of distinct non-null values.

## Exam reasoning

### Identify the exact implementation and operation

Do not infer mutation support merely from a List reference. Check whether it came from ArrayList, Arrays.asList, List.of, a wrapper or a view. Distinguish element replacement from structural modification and distinguish backing changes from direct writes through a wrapper.

### Follow the equality mechanism

HashSet uses equality/hashing, while TreeSet uses its ordering relation for membership. A comparator that ignores a field can collapse values that equals distinguishes. Equal hash codes alone do not make objects equal; collisions must still be resolved by the collection.

### Check compile-time generic permissions first

Before tracing runtime values, ask whether adding or assigning the value is legal through the declared wildcard type. Extends does not mean “accept any subclass for insertion.” Super does not promise that retrieved elements have the most specific lower-bound type. Use the direction of information flow to reason about the operation.

## Cheatsheet

| Concept | Key distinction |
| --- | --- |
| List / Set / Map | Sequence / uniqueness / key-value association |
| Generic invariance | List<Integer> is not List<Number> |
| PECS | Extends for producers; super for consumers |
| Wildcard capture | Preserve an unknown type through a helper |
| Erasure | Runtime representation does not retain every generic parameter |
| Heap pollution | Unsafe boundaries can cause later retrieval failures |
| Comparator | Zero can establish sorted-collection membership equivalence |
| Mutable keys | Changing equality/hash state can break lookup assumptions |
| Unmodifiable view | Blocks writes through the view, not changes through the owner |
| Snapshot copy | Copies membership, not necessarily mutable element state |
| Arrays.asList | Fixed-size, array-backed list |
| SubList | Backed view with structural-modification constraints |
| Fail-fast iteration | Bug detection, not concurrency control |
| Concurrent iteration | Read the specific weak/snapshot consistency contract |
| ConcurrentHashMap | Atomic operations differ from separate get/put calls |
| CopyOnWriteArrayList | Cheap stable traversal; expensive writes |
| Performance | Include lookup, allocation, locality, sizing and contention |
| Cache design | Thread safety does not provide eviction or bounded memory |

## Check yourself

### 1. Producer wildcard

Why can a List<? extends Number> produce Number values but not accept an arbitrary Integer?

**Answer:** Its actual element type might be another Number subtype. Reading as Number is safe; inserting Integer would violate some possible underlying list types.

### 2. View or snapshot

Why does example G3's unmodifiable view grow while its copy does not?

**Answer:** The view delegates to the modified backing list. The copy captured its own membership at creation, although mutable elements would still require separate ownership reasoning.

### 3. Advanced: TreeSet loses a value

A comparator compares only string length. Why does adding dog after cat not increase set size?

**Answer:** The comparator returns zero, so the sorted set treats them as ordering-equivalent members. Add a tie-breaker when the full string identity must distinguish them.

### 4. Advanced: mutable map key

A key changes a field used by hashCode after insertion. Why can lookup fail while iteration still exposes the entry?

**Answer:** The entry remains stored under assumptions established by its earlier hash/equality state. Mutation has broken the lookup contract rather than cleanly removed the entry.

### 5. Advanced: synchronized individual operations

Two threads each perform get followed by put on a concurrent map to increment a value. Is the whole increment necessarily atomic?

**Answer:** No. Separate individually safe operations do not form one atomic read-modify-write sequence. Use an appropriate atomic map operation or an explicitly coordinated invariant.

### 6. Iterator exception as a lock

Can a program rely on a fail-fast iterator throwing ConcurrentModificationException to coordinate concurrent writers?

**Answer:** No. Fail-fast behavior is a diagnostic aid, not a synchronization or visibility guarantee. Choose a valid concurrency policy and a collection with the required contract.

## Sources

Reviewed 2026-09-25. Baseline: Java SE 17; sequenced collections belong to the Java 21 chapter.

- [Collection API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Collection.html).
- [HashMap](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html).
- [TreeSet](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/TreeSet.html).
- [Comparator](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Comparator.html).
- [List](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html).
- [Collections wrappers](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Collections.html).
- [ConcurrentHashMap](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html).
- [CopyOnWriteArrayList](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html).
- [Wildcard guidelines](https://docs.oracle.com/javase/tutorial/java/generics/wildcardGuidelines.html).
- [Non-reifiable types and heap pollution](https://docs.oracle.com/javase/tutorial/java/generics/nonReifiableVarargsType.html).
