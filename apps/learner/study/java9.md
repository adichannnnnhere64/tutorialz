## Understand

### Modules are explicit boundaries

Java 9 introduced the Java Platform Module System, or JPMS. A module groups packages and declares which other modules it reads and which packages it exposes. Readability is the dependency relationship: a requires directive lets one module read another. Accessibility also depends on package exports and ordinary Java visibility. A public class in an unexported package is not automatically a public API for other modules.

Exports enables ordinary access to public types in a package. Opens enables deep reflection into a package at runtime, subject to the reflective API's rules. A framework reading private entity fields may require an opened package even when application code already compiles against exported types. Exporting every package is not a substitute for opening the specific package a framework reflects over. Qualified exports and opens restrict the target modules; use the narrowest boundary compatible with the integration.

Every named module implicitly reads java.base. Requires transitive exposes a dependency's readability to downstream readers, useful when that dependency appears in an exported API. Requires static means the dependency is required at compile time but optional for runtime resolution. It does not make code safe to execute without the dependency. The application still needs a path that avoids unavailable classes when the optional feature is absent.

### Small APIs with important contracts

List.of, Set.of, and Map.of create unmodifiable collections and reject null elements, keys, or values as applicable. Set factories reject duplicate arguments; map factories reject duplicate keys. Their elements may still refer to mutable objects. Do not predict Set.of or Map.of iteration order, and do not confuse unmodifiable structure with deep immutability. These factories are not replacements for a mutable accumulation buffer.

Java 9 also added private interface methods, JShell, Flow, enhanced try-with-resources, and new stream/Optional operations. Private interface helpers share implementation among defaults without becoming methods implementers inherit. JShell supports interactive exploration, but a successful snippet is not a substitute for compiling a complete project with its declared release and dependencies. Experimental or incubating APIs must be distinguished from finalized Java SE APIs when planning deployment.

## Apply

### Example J9A: A matching prefix is not a filter

Complete Java 9 program; expected output: `2,4`.

```java
import java.util.stream.*;
class Main {
  public static void main(String[] args) {
    String result = Stream.of(2, 4, 1, 6)
        .takeWhile(n -> n % 2 == 0)
        .map(String::valueOf).collect(Collectors.joining(","));
    System.out.print(result);
  }
}
```

For this ordered source, takeWhile stops at the first nonmatching element. Filter would also keep six, while dropWhile would retain one and six. The predicate is the same but the operation's contract changes the result. On an unordered stream, do not assume a source prefix has the same meaning. Ordering is part of the question, not an incidental implementation detail.

### Example J9B: Flatten optional results

Complete Java 9 program; expected output: `Ada,Lin`.

```java
import java.util.*;
import java.util.stream.*;
class Main {
  public static void main(String[] args) {
    String names = Stream.of(Optional.of("Ada"), Optional.<String>empty(),
                             Optional.of("Lin"))
        .flatMap(Optional::stream).collect(Collectors.joining(","));
    System.out.print(names);
  }
}
```

Optional.stream produces zero or one elements. Flattening therefore removes absent results without calling get on them. This is a Java 9 operation, even though streams and Optional themselves appeared in Java 8. If absence represents invalid data rather than a permissible missing result, silently dropping it would be the wrong domain behavior despite being concise code.

### Example J9C: Unmodifiable is not deeply immutable

Complete Java 9 program; expected output: `2:blocked`.

```java
import java.util.*;
class Main {
  public static void main(String[] args) {
    List<String> inner = new ArrayList<>();
    inner.add("first");
    List<List<String>> outer = List.of(inner);
    inner.add("second");
    System.out.print(outer.get(0).size() + ":");
    try { outer.add(new ArrayList<>()); }
    catch (UnsupportedOperationException expected) { System.out.print("blocked"); }
  }
}
```

The outer list rejects structural modification, yet the contained list remains mutable through its original reference. A safe snapshot of nested mutable data requires a deliberate copying policy at every relevant layer. Copying one container does not copy the entire graph, and the right depth depends on what callers are allowed to mutate.

### Example J9D: A narrow module descriptor

Illustrative module-info.java; this fragment requires the named application packages and API module, so it is not a standalone Main program.

```java
module billing.service {
  requires java.sql;
  requires transitive billing.api;
  exports billing.service.facade;
  opens billing.service.entities to org.hibernate.orm.core;
}
```

Consumers can compile against the facade and also read billing.api through the transitive dependency. Hibernate can reflect into the entity package without making that package ordinary exported API. The example is a boundary sketch, not a complete deployable Hibernate application: real module names, versions, dependencies, and provider configuration must be verified from the selected artifacts.

## Advanced

### Named, automatic, and unnamed modules

A modular JAR has a module descriptor. A nonmodular JAR on the module path can become an automatic module, with a name supplied by its manifest or derived from its filename. Stable Automatic-Module-Name metadata is safer than depending on a filename-derived name that changes after packaging. Class-path code belongs to unnamed modules. Moving the same dependency between the class path and module path can change visibility and resolution behavior.

Automatic modules are a migration bridge, not equivalent to a carefully encapsulated explicit module. Split packages and accidental duplicate classes often emerge during modularization because previously flat class paths allowed ambiguous packaging to remain hidden. Inspect the actual resolved graph and application packaging rather than adding arbitrary exports until compilation passes. Separate platform module changes from an application server's own class-loader hierarchy; the two mechanisms can interact but are not synonyms.

Services decouple an interface from provider discovery. A consumer module declares uses for the service; a provider declares provides with its implementation. This allows substitution without hard-coding the implementation module into business logic. Service discovery still requires the provider to be present and resolved appropriately. Test packaging of service metadata, particularly when shading JARs or building a custom runtime image.

### Flow demand, cancellation, and signals

Flow defines Publisher, Subscriber, Subscription, and Processor interfaces for demand-controlled item delivery. Demand is additive: requesting two, receiving one, and requesting three leaves four outstanding. Nonpositive demand is an error rather than a request to pause. A subscriber controls demand through its subscription; requesting Long.MAX_VALUE can be treated as effectively unbounded.

Cancellation is best-effort. Already in-flight items may still arrive, and cancellation does not promise a later onComplete or onError. Subscriber callbacks need a clear policy for resource cleanup without assuming that terminal notification will arrive after cancellation. The interface set does not by itself create nonblocking I/O, a broker, durable messages, or an application-wide retry policy. Backpressure at one boundary does not prevent unbounded buffering elsewhere.

Signal serialization and ordering must be respected by implementations. Avoid writing a publisher casually by invoking callbacks from arbitrary threads: reentrant demand, concurrent cancellation, overflow, and terminal-state races complicate the protocol. Use a tested implementation when production reliability matters. Flow is distinct from JMS: JMS specifies messaging-provider contracts, whereas Flow models in-process or adapted reactive stream interaction.

### Multi-release JARs and runtime images

A multi-release JAR declares Multi-Release: true in its manifest and can place version-specific classes under META-INF/versions/N. A supporting runtime selects the highest applicable versioned entry not exceeding its own version, falling back to the base entry where appropriate. It does not simply select the newest class present. Keep base classes compatible with the oldest supported runtime and maintain the public API consistency required by the JAR specification.

Jdeps helps inspect dependencies and internal API use; jlink assembles a runtime image from modules. Neither guarantees the application has all reflective, service-loaded, native, configuration, or external resources it needs. Test the image with realistic features enabled. A minimal image that starts but cannot load the production database driver is not a successful deployment.

## Production

### Migrate incrementally and keep evidence

Inventory runtime versions, dependency bytecode levels, reflective access, and use of removed or internal APIs before moving a Java 8 application. Compile with --release for the intended target; source and target alone do not prevent accidental compilation against newer APIs. Keep a migration test matrix that includes the real server, instrumentation agents, JSON library, persistence provider, and TLS configuration.

Treat --add-opens and --add-exports as explicit compatibility exceptions with owners and removal criteria. They can unblock a dependency temporarily, but broad flags weaken encapsulation and hide upgrade work. An illegal-access warning or InaccessibleObjectException should lead to identifying the component and required package, not automatically opening every module. Later JDKs tightened encapsulation beyond Java 9's transitional behavior.

### Operate bounded reactive pipelines

Document buffer sizes, overflow policy, demand replenishment, cancellation, and error handling for every asynchronous handoff. If a slow subscriber causes a publisher to buffer indefinitely, the application has moved its capacity problem rather than solved it. Decide whether to block, reject, drop replaceable observations, or persist durable business work. Those choices have different correctness implications.

Metrics should distinguish accepted input, delivered items, processing completion, cancellation, and dropped items. A subscriber requesting one item at a time can still start unlimited asynchronous operations if it requests again before the previous operation completes. Tie demand to actual processing capacity. Test slow consumers and shutdown races deliberately, rather than relying on a happy-path demonstration of fluent APIs.

## Exam reasoning

### Separate compilation, access, and execution

For module questions, ask whether the source module reads the target, whether the target exports the package, and whether ordinary visibility permits access. Reflection into private members introduces an opens question. A public modifier alone is insufficient, while opening a package does not automatically make ordinary source references legal.

For collections, first check nulls and duplicate keys, then mutability and element aliasing. A call may fail during factory creation before any later mutation is attempted. For streams, identify ordered versus unordered behavior before predicting takeWhile or dropWhile results. For Flow, maintain a simple demand ledger and distinguish cancellation from successful completion.

For release questions, distinguish feature introduction from later refinement. Java 9 includes the module system but not records, virtual threads, or Stream.toList. The HTTP client shipped as an incubating module in Java 9 and became standard in Java 11. A question omitting those boundaries should not lead you to assume that a current API existed unchanged in every earlier release.

## Cheatsheet

| Topic | Key boundary |
| --- | --- |
| requires | Read another module |
| requires transitive | Downstream readers also read the dependency |
| requires static | Compile-time requirement; optional runtime resolution |
| exports | Ordinary public API access |
| opens | Runtime deep reflection |
| uses / provides | Service consumer / service implementation declaration |
| List.of / Set.of / Map.of | Unmodifiable and null-rejecting; not deeply immutable |
| takeWhile / dropWhile | Prefix-sensitive on ordered streams |
| Optional.stream | Zero or one elements |
| Flow.request | Add positive demand |
| Flow.cancel | Best-effort; no guaranteed terminal callback |
| Multi-release JAR | Highest eligible versioned entry, otherwise base |
| --release | Language, bytecode, and supported API target together |
| jlink | Assemble runtime image; still test dynamic dependencies |

## Check yourself

### 1. Export or open

A framework needs private entity-field reflection. Is exports alone sufficient?

**Answer:** No. The relevant package generally needs to be opened to the framework module for deep reflection. Ordinary exported public access and reflective access solve different problems.

### 2. Demand arithmetic

Request two, receive one, then request three. How much demand remains?

**Answer:** Four. Request increments outstanding demand rather than replacing it. Completion or error may still end the stream before all requested items arrive.

### 3. Collection element mutation

Does List.of prevent mutation of a mutable object stored inside it?

**Answer:** No. It prevents list modification, not changes to the referenced object's internals. Use suitable immutable values or defensive copies for a true snapshot.

### 4. Advanced: cancellation cleanup

Can cleanup rely exclusively on onComplete after cancelling a Flow subscription?

**Answer:** No. Cancellation need not produce a terminal callback. The subscriber must arrange cleanup according to its ownership policy while handling possible in-flight signals safely.

### 5. Advanced: JAR selection

A multi-release JAR has base, version-nine, and version-seventeen implementations. Which runs on Java 11?

**Answer:** The eligible version-nine implementation, assuming a valid multi-release JAR and the relevant entry exists. Version seventeen is too new; the runtime does not select it merely because it is the highest entry.

### 6. Advanced: optional dependency

Does requires static make it safe to execute code using a missing runtime dependency?

**Answer:** No. It changes resolution requirements, not the existence of classes. Guard the optional feature and package/test its enabled and disabled paths explicitly.

## Sources

Reviewed 2026-09-25. Baseline: Java 9; later encapsulation and API changes are labeled. Module descriptor example is illustrative, not a standalone application.

- [Java 9 modules and packages](https://docs.oracle.com/javase/specs/jls/se9/html/jls-7.html)
- [ModuleDescriptor](https://docs.oracle.com/javase/9/docs/api/java/lang/module/ModuleDescriptor.html)
- [Flow](https://docs.oracle.com/javase/9/docs/api/java/util/concurrent/Flow.html)
- [Flow subscription demand and cancellation](https://docs.oracle.com/javase/9/docs/api/java/util/concurrent/Flow.Subscription.html)
- [Java 9 Stream](https://docs.oracle.com/javase/9/docs/api/java/util/stream/Stream.html)
- [Java 9 List](https://docs.oracle.com/javase/9/docs/api/java/util/List.html)
- [Multi-release JAR specification](https://docs.oracle.com/javase/9/docs/specs/jar/jar.html)
- [Java 9 tool specifications](https://docs.oracle.com/javase/9/tools/toc.htm)
