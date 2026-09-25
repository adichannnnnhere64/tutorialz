## Understand

### Functional interfaces and lambda meaning

Java 8 added lambdas, method references, default interface methods, streams, Optional, and the modern date/time API. A lambda supplies the behavior of a functional interface: an interface with one abstract method after the language's inheritance rules are applied. Default and static methods do not add abstract obligations. Methods corresponding to public Object methods do not count toward the functional-interface method requirement. The annotation FunctionalInterface asks the compiler to check the intention; it does not create that property.

A lambda gets its parameter and return types from its target context. An overloaded call accepting two different functional interfaces can therefore be ambiguous even when the lambda body looks obvious to a human. Give a variable an explicit interface type or use a cast when a legitimate overload needs disambiguation. Avoid API overloads distinguished only by nearly identical functional interfaces. Checked exceptions must fit the target method's throws clause; a lambda does not automatically convert them into unchecked exceptions.

Captured local variables must be final or effectively final. This restricts reassignment of the variable, not mutation of an object it references. Capturing an ArrayList and modifying it from several workers is still shared mutation. Lambda this refers to the enclosing instance, unlike this inside an anonymous inner class. Method references are concise behavior adapters, not a separate execution model or a guarantee of deferred evaluation of every expression used to create them.

### Stream pipelines and values

A stream is a single-use computation over a source, not another collection. Intermediate operations describe transformations; a terminal operation drives evaluation. Filter changes membership, map changes values, and flatMap converts each input into zero or more outputs and flattens the result. Primitive streams avoid some boxing and offer numeric operations directly. A short-circuiting terminal operation may stop early; do not put required business side effects into a pipeline stage that might never process every element.

Optional represents a result that may be absent. It is most useful at a return boundary where absence is meaningful. It is not a universal replacement for fields, parameters, validation errors, or every null in a framework model. A method returning Optional should return an Optional instance, never null. Use composition to describe how absence propagates, and choose whether missing data is expected or an actual business failure.

## Apply

### Example J8A: Filter, transform, and aggregate

Complete Java 8 program; expected output: `2:10`.

```java
import java.util.*;
import java.util.stream.*;
class Main {
  public static void main(String[] args) {
    List<Integer> doubled = Arrays.asList(1, 2, 3).stream()
        .filter(n -> n > 1).map(n -> n * 2)
        .collect(Collectors.toList());
    int sum = doubled.stream().mapToInt(Integer::intValue).sum();
    System.out.print(doubled.size() + ":" + sum);
  }
}
```

Filtering retains two and three; mapping produces four and six. Collection creates a result, then a new stream computes its sum. Reusing the first stream after its terminal operation would be invalid. Collectors.toList does not promise a particular implementation or mutability contract. When an actual ArrayList is required, request it through toCollection rather than casting the result.

### Example J8B: Define duplicate-key behavior

Complete Java 8 program; expected output: `5`.

```java
import java.util.*;
import java.util.stream.*;
class Main {
  public static void main(String[] args) {
    Map<String, Integer> counts = Arrays.asList("aa", "aaa").stream()
        .collect(Collectors.toMap(s -> s.substring(0, 1),
                                  String::length, Integer::sum));
    System.out.print(counts.get("a"));
  }
}
```

Both strings map to the same key. The merge function combines lengths rather than silently choosing an arbitrary entry. Without a merge function, duplicate keys cause failure. The correct policy depends on the domain: adding quantities may be right, while merging two user accounts by keeping the first is likely a defect. Do not treat an implementation convenience as a business rule.

### Example J8C: Observe eager fallback evaluation

Complete Java 8 program; expected output: `ready:ready:1`.

```java
import java.util.Optional;
class Main {
  static int calls;
  static String fallback() { calls++; return "fallback"; }
  public static void main(String[] args) {
    Optional<String> value = Optional.of("ready");
    String a = value.orElse(fallback());
    String b = value.orElseGet(Main::fallback);
    System.out.print(a + ":" + b + ":" + calls);
  }
}
```

The argument passed to orElse is evaluated before the method is called, even though it is not selected. OrElseGet receives a supplier and invokes it only when needed. This matters for expensive lookups and side effects. Neither choice should conceal a missing required value; orElseThrow with a suitable supplier can express a required result in Java 8.

### Example J8D: Resolve unrelated default methods

Complete Java 8 program; expected output: `left+right`.

```java
interface Left { default String label() { return "left"; } }
interface Right { default String label() { return "right"; } }
class Main implements Left, Right {
  public String label() { return Left.super.label() + "+" + Right.super.label(); }
  public static void main(String[] args) { System.out.print(new Main().label()); }
}
```

Unrelated inherited defaults with the same signature require an explicit resolution. A class method generally takes precedence over an interface default, and a more specific interface declaration can take precedence over a less specific one. These rules preserve understandable inheritance; default methods do not introduce multiple inheritance of instance fields.

## Advanced

### Reduction laws and collector design

Reduction needs an associative operation so regrouping does not change the meaning. Integer addition works within Java's arithmetic rules, while subtraction is not associative. Floating-point addition can exhibit rounding differences after regrouping. An identity must leave a value unchanged: adding ten is not an identity for sum. A parallel reduction can apply its identity to multiple partitions, exposing errors that a sequential run appeared to tolerate.

A collector separates container creation, element accumulation, combination, and optional finishing. Non-concurrent collectors can safely use ordinary mutable containers because the stream implementation confines partial containers and combines them appropriately. This is why collecting into lists is different from mutating one external ArrayList in parallel forEach. Characteristics such as CONCURRENT, UNORDERED, and IDENTITY_FINISH are claims about the implementation, not switches that magically make unsafe code correct.

Use groupingBy with a downstream collector when the desired result is an aggregate per key rather than a list of all matching objects. Summing or counting downstream can reduce retained memory. GroupingByConcurrent changes accumulation characteristics, but does not make arbitrary downstream values safely mutable by callers after collection. Review the resulting map and value contracts separately. Never assume a hash-based map supplies a stable business presentation order.

### Ordering, state, and interference

Encounter order comes from the source and operations, not from the order in which worker threads finish. FindFirst respects encounter order when defined; findAny permits a less constrained result. Parallel forEach does not preserve encounter order, while forEachOrdered does. Ordered distinct, sorting, and limit may require coordination or buffering. Parallel execution is therefore not automatically faster, especially for small collections or expensive synchronization.

Non-interference means not modifying the stream's source during traversal unless its contract explicitly supports the relevant concurrent behavior. Stateless functions do not rely on mutable state that changes during evaluation. An atomic counter in a mapping function may avoid a data race yet still make results depend on scheduling. Thread safety and deterministic stream semantics are related but different questions. Prefer transforming elements from their own values.

### Optional composition and date/time boundaries

Map transforms a present Optional value; flatMap is for a function already returning Optional. Optional.map turns a null mapping result into absence, while flatMap expects the mapper to return a non-null Optional. Java 8 lacks Optional.stream and ifPresentOrElse; those arrived in Java 9. Avoid identity comparison or synchronization on Optional instances because they are value-based containers, not identity tokens.

Java.time separates machine timestamps from human calendar representations. Instant is a point on the timeline; LocalDate is a date without a zone; LocalDateTime is not enough to identify an instant during ambiguous local times. Duration measures elapsed time and Period describes calendar amounts. A day added to zoned calendar time can span twenty-three or twenty-five hours around daylight-saving transitions. Inject a Clock for repeatable date-dependent tests rather than reading the current time deep inside business logic.

## Production

### Keep functional code observable

Prefer small named functions when a pipeline becomes hard to debug or describes several different business decisions. A long chain is not inherently better than an explicit loop. Separate validation, transformation, and side-effecting persistence when their failure and retry policies differ. If processing ten thousand records fails halfway through, know which effects have committed; a stream terminal operation does not provide a transaction boundary by itself.

Do not use peek for mandatory audit logging or essential updates. It is intended for observation during traversal, and evaluation can stop early or be optimized according to the pipeline contract. Explicitly return the data needed for a later effect or perform the effect in a clearly owned operation. Resource-backed streams, such as Files.lines, require closure using try-with-resources; ordinary collection streams do not own an open file handle.

### Decide when parallelism pays

Measure representative workloads before enabling parallel streams. CPU-intensive independent transformations may benefit; blocking database or HTTP calls can occupy shared execution resources and overload dependencies. Consider task size, splitting quality, ordering constraints, allocation, and downstream capacity. A benchmark that creates unrealistic tiny objects or ignores warmup can produce misleading conclusions. Use a dedicated execution design when isolation, admission control, deadlines, or context propagation matter.

Compile genuinely Java 8-targeted code with a release-aware toolchain. Newer source syntax is not the only compatibility risk: calling List.of or Stream.toList links against APIs absent in Java 8. Check dependency bytecode levels and runtime libraries as well. Migration tests should include serialization, reflection, locale/time-zone assumptions, and framework integration rather than just the compiler's acceptance of application classes.

## Exam reasoning

### Trace the contract, not a familiar-looking output

First identify the Java version, source order, intermediate stages, terminal operation, and any shared mutable state. A missing terminal operation normally means no element processing has happened. A second terminal operation on the same stream is invalid. A pipeline over an unordered source cannot promise the first inserted item merely because a local run returned it.

For reduction questions, test the proposed identity with one value and test associativity with three values. For collectors, identify who owns each mutable container and whether the combiner is compatible with accumulation. For Optional, distinguish eager argument evaluation from deferred supplier invocation. For default methods, inspect the complete inheritance hierarchy before choosing the implementation.

A credible answer explains why competing choices fail. “Use parallel because it is faster” ignores cost and ordering. “Use synchronizedList because streams require thread-safe lists” ignores partition confinement. “Use get because Optional prevents null” ignores absence. Prefer the answer whose guarantees match the stated constraint without inventing extra assumptions.

## Cheatsheet

| Feature | Precise distinction |
| --- | --- |
| Predicate / Function | Test a value / transform a value |
| Consumer / Supplier | Consume input / provide a result |
| Captured local | Effectively final variable, not deeply immutable object |
| map / flatMap | One mapped value / flatten zero-or-more results |
| reduce | Associative combination with a valid identity |
| collect | Mutable reduction with supplier, accumulator, combiner |
| toMap | Define duplicate-key policy explicitly |
| findFirst / findAny | Encounter-order first / permitted arbitrary match |
| forEachOrdered | Ordered action, not a guarantee of useful parallel speedup |
| orElse / orElseGet | Eager argument / deferred fallback |
| Default method | Behavior inheritance; resolve unrelated conflicts |
| Java 9 boundary | Optional.stream, takeWhile, List.of are not Java 8 |
| Java 16 boundary | Stream.toList is not Java 8 Collectors.toList |

## Check yourself

### 1. Captured list

Can a lambda capture a local list and then modify its contents?

**Answer:** Yes if the variable remains effectively final. The rule prevents reassignment, not mutation. Concurrent use still requires an appropriate ownership or synchronization policy.

### 2. Stream reuse

Can a stream be counted and then collected?

**Answer:** Not the same stream instance. A terminal operation consumes it. Create a new stream from a reusable source, or collect once and inspect the result.

### 3. Optional fallback

Why does a fallback counter increase when orElse is called on a present value?

**Answer:** Java evaluates the argument before calling orElse. Use orElseGet to defer a fallback computation until absence, when deferred evaluation is the intended behavior.

### 4. Advanced: false identity

Why is reduce with identity ten and addition wrong for summing a parallel stream?

**Answer:** Ten is not the additive identity. Partitioned reduction can introduce it multiple times. Use zero and add an intentional adjustment separately if the business rule requires one.

### 5. Advanced: safe mutable collection

Why can Collectors.toList work in parallel although ArrayList is not thread-safe?

**Answer:** A non-concurrent collector uses confined partial containers and a combination protocol. This differs from several workers concurrently mutating one externally shared list.

### 6. Advanced: stable numbering

Does using AtomicInteger inside parallel map guarantee each item receives its encounter-order index?

**Answer:** No. It can make increments atomic while assignment order still follows scheduling rather than encounter order. Derive indices from an ordered indexed source or use an explicit sequential algorithm.

## Sources

Reviewed 2026-09-25. Baseline: Java 8; later additions are labeled. Explanations and examples are original learning material.

- [Lambda expressions](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html)
- [Functional interfaces](https://docs.oracle.com/javase/8/docs/api/java/lang/FunctionalInterface.html)
- [Stream package contracts](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html)
- [Collector laws and confinement](https://docs.oracle.com/javase/8/docs/api/java/util/stream/Collector.html)
- [Collectors](https://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html)
- [Optional](https://docs.oracle.com/javase/8/docs/api/java/util/Optional.html)
- [Default interface methods](https://docs.oracle.com/javase/tutorial/java/IandI/defaultmethods.html)
- [Java time](https://docs.oracle.com/javase/8/docs/api/java/time/package-summary.html)
