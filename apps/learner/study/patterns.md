## Understand

### Purpose, prerequisites and learning objectives

A design pattern describes a reusable organization of responsibilities, not a magic annotation or a requirement to add classes. Before studying this chapter, understand interfaces, overriding, composition, object identity and access control. The examples target Java 17 and use only the standard library. By the end, you should be able to identify a changing responsibility, choose a suitable pattern, explain its cost, and distinguish a pattern's intent from superficial code shape.

Separate creation, structure and behavior. Creational patterns decide how objects become available. Structural patterns arrange objects and interfaces. Behavioral patterns arrange collaboration, algorithms and state transitions. A system can use several patterns together: a factory can create a decorated strategy, and a command can invoke a facade. Explain each responsibility independently instead of trying to assign one label to the entire application.

### Simple Factory, Factory Method and Abstract Factory

“Factory” is an umbrella term. A Simple Factory centralizes a creation decision, often in a switch or static method. It is useful terminology but is not a separate member of the classic 23-pattern GoF catalog. Adding a static `create` method does not automatically implement Factory Method.

Factory Method gives a creator an overridable creation operation. The creator's workflow depends on a product interface; subclasses supply the concrete product. The variation point is which product a creator makes. Abstract Factory supplies several related product types through one family interface. Its variation point is a compatible family, such as platform-specific buttons and menus. It helps prevent accidental mixing, but ordinary Java interfaces do not automatically prove that arbitrary implementations return mutually compatible products.

### Builder and construction invariants

Builder separates assembling a product from using the finished product. A Java fluent builder commonly collects optional settings and checks cross-field invariants when `build()` is called. The original pattern can also support different representations and a director that coordinates construction steps; a director is not mandatory in every practical builder.

A builder should not leak a partially valid product. Copy mutable inputs, validate required values, and decide whether builder instances are reusable. Fluent setters alone do not establish immutability. Returning the builder's mutable collection directly lets later builder changes corrupt an already-built object.

## Apply

### Example P1: Simple Factory

Complete Java 17 program; expected output: `csv`.

```java
class Main {
  interface Exporter { String format(); }
  static Exporter create(String kind) {
    return switch (kind) {
      case "csv" -> () -> "csv";
      case "json" -> () -> "json";
      default -> throw new IllegalArgumentException("Unknown format");
    };
  }
  public static void main(String[] args) {
    System.out.print(create("csv").format());
  }
}
```

The switch is intentionally centralized. Callers do not know concrete implementation classes. Adding another format changes this factory, which can be acceptable for a small closed set. If plugins must register independently, use an explicit registry or service-provider mechanism with validation. Do not replace a readable two-case decision with an elaborate hierarchy solely to satisfy a pattern name.

### Example P2: Factory Method

Complete Java 17 program; expected output: `report:pdf`.

```java
class Main {
  interface Document { String format(); }
  abstract static class ReportJob {
    protected abstract Document createDocument();
    final String run() {
      Document document = createDocument();
      return "report:" + document.format();
    }
  }
  static final class PdfJob extends ReportJob {
    protected Document createDocument() { return () -> "pdf"; }
  }
  public static void main(String[] args) {
    System.out.print(new PdfJob().run());
  }
}
```

The inherited workflow remains fixed, while product creation is overridden. This combines a Factory Method with a template-like workflow. A production workflow would use the product for actual rendering and establish ownership of any resources it opens. Subclassing is a cost: if creation must vary independently at runtime, injecting a supplier or an Abstract Factory may be easier to compose.

### Example P3: Abstract Factory

Complete Java 17 program; expected output: `dark:dark`.

```java
class Main {
  interface Button { String theme(); }
  interface Menu { String theme(); }
  interface WidgetFactory {
    Button button();
    Menu menu();
  }
  static final class DarkWidgets implements WidgetFactory {
    public Button button() { return () -> "dark"; }
    public Menu menu() { return () -> "dark"; }
  }
  public static void main(String[] args) {
    WidgetFactory factory = new DarkWidgets();
    System.out.print(factory.button().theme() + ":" + factory.menu().theme());
  }
}
```

Selecting one family factory avoids two unrelated configuration decisions. Adding a new family is straightforward: implement the same product-producing operations. Adding a new product type is more disruptive because the factory interface and every implementation may need to change. That is the central extension tradeoff to discuss in an architecture review.

### Example P4: Builder with defensive copying

Complete Java 17 program; expected output: `1:3`.

```java
import java.util.*;
class Main {
  record Job(List<String> recipients, int retries) {
    Job {
      recipients = List.copyOf(recipients);
      if (recipients.isEmpty() || retries < 0)
        throw new IllegalArgumentException("Invalid job");
    }
  }
  static final class JobBuilder {
    private final List<String> recipients = new ArrayList<>();
    private int retries;
    JobBuilder to(String value) {
      recipients.add(Objects.requireNonNull(value));
      return this;
    }
    JobBuilder retries(int value) { retries = value; return this; }
    Job build() { return new Job(recipients, retries); }
  }
  public static void main(String[] args) {
    JobBuilder builder = new JobBuilder().to("ops@example.test").retries(3);
    Job job = builder.build();
    builder.to("audit@example.test");
    System.out.print(job.recipients().size() + ":" + job.retries());
  }
}
```

The built job owns an unmodifiable snapshot of the list. Changing the builder afterward does not change that job. The record is safe here because its elements are immutable strings; copying a list of mutable objects would still leave shared element state. The builder itself is not thread-safe and is intended for one construction flow.

## Advanced

### Prototype and Singleton

Prototype creates from an existing configured instance when rebuilding its configuration would be cumbersome. Define what copying means: duplicated containers, shared immutable values, and ownership of mutable children. Java's shallow object cloning is not a universal deep-copy mechanism. Copy constructors or explicit copy operations often make the intended boundary easier to inspect.

Singleton constrains instance availability within a defined scope. Class-loader identity, application contexts, processes and clusters create different scopes. An enum or initialization holder can solve some Java instance-initialization problems; it does not make business operations atomic or elect one owner across a cluster. Prefer explicit dependency lifetimes when global state would interfere with testing, tenant isolation or shutdown.

### Adapter, Bridge and Composite

Adapter translates an existing incompatible interface into one a client expects. Translate semantics as well as method names: units, exceptions, cancellation and ownership can differ. Bridge separates an abstraction hierarchy from an implementation hierarchy so they vary independently, such as different report types using different rendering backends.

Composite treats leaves and groups through a common operation. A file tree or organization hierarchy can be traversed uniformly, but the interface should not promise nonsensical operations on every leaf. Decide how cycles, duplicate membership and aggregate errors are handled before assuming every object graph is a tree.

### Decorator, Facade, Flyweight and Proxy

Decorator preserves an interface while adding behavior around a delegate. Ordering matters: compress-then-encrypt is not equivalent to encrypt-then-compress, and authorization should not disappear behind a cached response. Facade offers a simpler subsystem entry point; it should not become an unbounded collection of unrelated business rules.

Flyweight shares intrinsic, reusable state and leaves context-specific state outside the shared object. A glyph's shape can be shared while each placement's coordinates remain external. Verify that the shared state is actually immutable or correctly synchronized.

Proxy manages access to a subject. It may add remote access, authorization or lazy initialization, but interface similarity does not preserve latency or failure behavior. Remote proxies need explicit timeouts, failure handling and appropriately coarse operations. A local-looking getter can still perform network I/O.

### Chain of Responsibility, Command and Interpreter

Chain of Responsibility lets candidate handlers process, reject or forward a request. Specify whether processing stops after one handler or intentionally continues through a pipeline. Missing a terminal decision in an authorization chain can become a security defect.

Command packages an operation and its receiver/context. It can support queues, logging and undo, but undo requires a defined inverse or saved state. A command object alone does not make execution durable, transactional or idempotent. Interpreter models evaluation of a small language using its grammar structure; for large languages, parsing tools and explicit resource limits are generally preferable to an expanding collection of recursive objects.

### Iterator, Mediator and Memento

Iterator separates traversal from collection representation. Its concurrency, removal and snapshot guarantees come from its contract, not the pattern name. Mediator centralizes collaboration among peers, reducing pairwise coupling; a mediator can itself become overly complex if unrelated workflows are combined.

Memento captures restorable state without exposing all representation details to its caretaker. Define snapshot completeness, retention and compatibility. Restoring a local object snapshot cannot automatically reverse a payment already submitted to another service.

### Observer, State and Strategy

Observer publishes changes to interested subscribers. Decide delivery order, synchronous versus asynchronous execution, failure isolation and unsubscribe lifecycle. A slow listener can block the publisher in a synchronous design; a forgotten listener can retain an entire object graph.

State delegates behavior according to an object's current state and legal transitions. Strategy delegates an interchangeable algorithm chosen by policy or configuration. Both can use composition, but state transitions describe the object's lifecycle whereas strategies usually represent alternative ways to perform a responsibility.

### Template Method and Visitor

Template Method fixes an algorithm skeleton while subclasses customize defined steps. Document which hooks may be overridden and avoid calling overridable methods from constructors before subclass initialization finishes. Strategy often provides a composition-based alternative when runtime replacement or independent extension is more important than inherited structure.

Visitor moves operations over a relatively stable element hierarchy into visitor implementations. Adding operations becomes easier; adding a new element type can require changing all visitors. Java overloading alone is resolved using compile-time argument types, so an element's `accept` method commonly participates in the dispatch arrangement. Sealed types and pattern matching offer another tradeoff for some closed hierarchies, not a universal replacement.

## Production

### Failure case: a remote proxy creates an N+1 request pattern

Suppose an order screen displays 100 orders and calls ten remote getters per order. Even though the code looks object-oriented, it can generate 1,000 network operations. Measure request counts and end-to-end latency. Introduce a bounded summary endpoint or batch operation, then define pagination, partial failures and authorization for every returned order. Caching proxy objects does not cache the remote data automatically.

### Failure case: a builder leaks mutable state

A report builder returns a report containing its own mutable options map. Reusing the builder changes an already-scheduled report. Reproduce the bug by building, mutating the builder, and asserting that the old product stays unchanged. Fix ownership with an appropriate copy and validate at the product boundary. A shallow unmodifiable wrapper over the original mutable map does not establish a snapshot.

### Failure case: retrying a command charges twice

A queue redelivers a payment command after the acknowledgment is lost. Generating a fresh command object does not identify the same business operation. Use a stable operation identifier and a durable deduplication boundary that is atomic with the effect when feasible. For an external payment provider, coordinate its idempotency contract and persist recovery state. Keep retry policy separate from the command's representation.

### Choosing a pattern with evidence

State the expected variation, the invariants that must remain fixed, and the cost of the abstraction. A factory adds indirection; a visitor couples to the element set; a decorator chain complicates tracing. Use tests around contracts and observable behavior rather than tests that assert a particular number of implementation classes. Prefer an ordinary constructor when construction has no genuine variability or complexity.

## Exam reasoning

### Identify intent before naming structure

If one overridable operation creates a product for an inherited workflow, Factory Method is the strongest match. If one object creates parsers and renderers that must belong to the same family, consider Abstract Factory. If several inputs and construction stages produce one validated object, consider Builder. A single switch that returns implementations is normally a Simple Factory, even when its method is named `factoryMethod`.

### Similar-looking wrappers have different responsibilities

An Adapter changes the expected interface. A Decorator adds behavior while maintaining the interface. A Proxy controls access to the subject. A Facade presents a simpler subsystem API. Read the scenario's intent; identical delegation syntax does not prove the same pattern. More than one intent may legitimately appear in a production component.

### Do not invent guarantees from pattern names

Singleton does not imply cluster-wide uniqueness. Builder does not imply a deep-immutable product. Observer does not imply asynchronous delivery. Command does not imply successful undo or exactly-once execution. Factory Method does not imply that every invocation returns a fresh instance unless its contract says so. These are frequent reasoning traps because the extra guarantee sounds plausible but has not been established.

## Cheatsheet

| Pattern | Choose it when | Main tradeoff or trap |
| --- | --- | --- |
| Factory Method | Subclasses choose a workflow's product | Inheritance is the extension point |
| Abstract Factory | Related products must form a compatible family | Adding product kinds affects every factory |
| Builder | Assembly has stages, optional inputs or cross-field rules | Validate and copy mutable inputs |
| Prototype | Copy a configured instance | Define shallow versus deep ownership |
| Singleton | One instance is required in a defined scope | Not automatically thread-safe or cluster-wide |
| Adapter | Existing interfaces do not match | Translate semantics, not only signatures |
| Bridge | Abstraction and implementation vary independently | Two dimensions of indirection |
| Composite | Leaves and groups share an operation | Guard cycles and invalid leaf operations |
| Decorator | Add composable behavior around an interface | Order and identity can matter |
| Facade | Simplify interaction with a subsystem | Avoid a catch-all service |
| Flyweight | Many objects share intrinsic state | Keep contextual state external |
| Proxy | Control access to another subject | Local-looking calls can be remote |
| Chain of Responsibility | Handlers decide who processes a request | Define stopping and fallback rules |
| Command | Represent an action as an object | Undo and retry need explicit semantics |
| Interpreter | Evaluate a small language | Complexity and evaluation limits grow |
| Iterator | Traverse without exposing representation | Iterator concurrency guarantees vary |
| Mediator | Coordinate interactions among peers | Central complexity can accumulate |
| Memento | Restore a captured object state | External effects are not rolled back |
| Observer | Notify interested subscribers | Lifecycle, ordering and listener failures |
| State | Behavior depends on lifecycle state | Make allowed transitions explicit |
| Strategy | Swap algorithms behind a contract | Select policy and preserve invariants |
| Template Method | Fix workflow while overriding selected steps | Inheritance and fragile hooks |
| Visitor | Add operations to stable element types | New element types affect visitors |
| Simple Factory, not a separate GoF entry | Centralize a small creation decision | A static factory is not automatically Factory Method |

## Check yourself

### 1. Product family or construction stages?

A UI library must create matching buttons, menus and dialogs for several themes. Which creation pattern fits?

**Answer:** Abstract Factory groups related product creation. Builder is a better fit for assembling one complex product through stages, not for the family relationship itself.

### 2. Explain the Builder output

In example P4, the builder receives another recipient after the job is built. Why does the program still print one recipient?

**Answer:** The product constructor creates its own list snapshot. The later builder mutation changes a different list. This reasoning would not prove deep immutability if list elements were mutable objects.

### 3. Advanced: distinguish Factory Method from a name

A static method called `factoryMethod` switches on a string and returns an implementation. There is no creator subclass. What is missing for the demonstrated GoF Factory Method structure?

**Answer:** The overridable creation operation used by a creator workflow is absent. This is a Simple Factory arrangement; the method name is not evidence of the pattern.

### 4. Advanced: undo a remote operation

A Command implementation saves the previous local balance, then submits a bank transfer. Does restoring the saved balance undo the transfer?

**Answer:** No. The external effect needs its own supported reversal or compensation process. Memento-like local restoration cannot retract another system's committed work.

### 5. Advanced: choose the cheaper extension axis

A document hierarchy changes rarely, but new analysis operations are added weekly. Why might Visitor help, and what change would make it expensive?

**Answer:** It groups new operations outside stable elements. Frequent addition of new element types would require updating visitor interfaces and implementations, shifting the maintenance cost.

### 6. Diagnose Flyweight corruption

Shared glyphs cache character and font but also store the latest screen position. Different documents overwrite each other's layout. What should move?

**Answer:** Position is contextual, extrinsic state and should be supplied by each placement. The reusable drawing information can remain shared, subject to its own immutability and lifetime rules.

## Sources

Reviewed 2026-09-25. Examples are original Java 17 programs. Pattern names describe design intent, not Java-language guarantees.

- [GoF authors and publisher: catalog and taxonomy](https://www.informit.com/store/design-patterns-elements-of-reusable-object-oriented-9780201633610). Used to check the catalog, not to reproduce book prose or examples.
- [Java 8 Calendar.Builder API](https://docs.oracle.com/javase/8/docs/api/java/util/Calendar.Builder.html): a real standard-library construction API with explicit state rules.
- [Java 8 DocumentBuilderFactory API](https://docs.oracle.com/javase/8/docs/api/javax/xml/parsers/DocumentBuilderFactory.html): factory configuration and provider discovery; class names alone do not classify every collaborator.
- [Java 8 ServiceLoader API](https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html): service-provider discovery as an alternative to a growing creation switch.
- [Java 17 Object API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html): cloning, identity and equality contracts.
- [Java 17 List API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html): copy and unmodifiable-list contracts.
