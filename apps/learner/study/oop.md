## Understand

### Objects, contracts and learning objectives

The examples target Java 17. Review references, constructors, method calls and access modifiers first. Object-oriented design is not simply putting functions inside classes: it assigns responsibility for preserving valid state and defines contracts between collaborators. You should be able to explain substitution, identify the dispatch mechanism used by a call, and design equality and ownership rules that survive real application use.

An object combines state and behavior. Encapsulation means its public operations protect its invariants, not merely that fields are private. A private list returned directly by a getter can still be modified by callers. A constructor that accepts invalid values and hopes a later setter will repair them exposes a partially valid object. Establish invariants at creation and preserve them through every supported operation.

### Inheritance, interfaces and composition

Inheritance creates a subtype relationship with an advertised contract. If a client relies on a base operation accepting a particular input, a subtype that silently rejects that input can violate behavioral substitution even though the Java compiler accepts the override. Contracts include outcomes, allowed failures, ownership and relevant ordering—not only parameter types.

Composition delegates to collaborators rather than inheriting implementation. Prefer it when one object uses another service but is not naturally a substitutable instance of that service. Interfaces describe capabilities; an abstract class can also share state and implementation. Java allows one class superclass and multiple implemented interfaces. This syntax does not eliminate conflicting contracts or make every combination a sensible design.

### Visibility, final and immutability

Public, protected, package and private access establish different boundaries. Protected access across packages has additional subclass-related rules; it is not simply public access for any code that happens to hold a superclass reference. Keep implementation helpers as narrow as practical.

Final means different things in different positions: a variable cannot be reassigned, a method cannot be overridden, and a class cannot be subclassed. A final reference can still point to mutable state. Immutability requires a complete ownership design, including mutable inputs, returned values, inherited behavior and references reachable through fields.

## Apply

### Example O1: interface reference and overriding

Complete Java 17 program; expected output: `card`.

```java
class Main {
  interface Payment { String label(); }
  static class Card implements Payment {
    public String label() { return "card"; }
  }
  public static void main(String[] args) {
    Payment payment = new Card();
    System.out.print(payment.label());
  }
}
```

The reference type determines which member calls are available at compile time. The object's runtime class determines the selected overriding instance implementation. Substitution lets a caller depend on Payment without constructing every concrete payment implementation itself.

### Example O2: overloading and overriding in one expression

Complete Java 17 program; expected output: `base:child`.

```java
class Main {
  static class Base { String name() { return "base"; } }
  static class Child extends Base {
    @Override String name() { return "child"; }
  }
  static String pick(Base value) { return "base"; }
  static String pick(Child value) { return "child"; }
  public static void main(String[] args) {
    Base value = new Child();
    System.out.print(pick(value) + ":" + value.name());
  }
}
```

The overloaded pick call uses the argument expression's compile-time Base type. The instance name call dispatches to Child's override. Changing the runtime object does not make overload resolution repeat dynamically. Static methods and fields have their own hiding/access rules and do not behave like this overriding instance method.

### Example O3: value equality and hashing

Complete Java 17 program; expected output: `1`.

```java
import java.util.*;
class Main {
  record InvoiceKey(String tenant, long id) {}
  public static void main(String[] args) {
    Set<InvoiceKey> keys = new HashSet<>();
    keys.add(new InvoiceKey("north", 7));
    keys.add(new InvoiceKey("north", 7));
    System.out.print(keys.size());
  }
}
```

The record's generated equality and hash behavior use its components. Two separately allocated keys with equal components represent one set member. The tenant component is important: omitting a dimension of business identity can merge distinct entities even though the Java equality implementation is internally consistent.

### Example O4: enforce an invariant at the operation boundary

Complete Java 17 program; expected output: `100`.

```java
class Main {
  static final class Balance {
    private int amount = 100;
    void withdraw(int value) {
      if (value < 0 || value > amount)
        throw new IllegalArgumentException("Invalid withdrawal");
      amount -= value;
    }
    int amount() { return amount; }
  }
  public static void main(String[] args) {
    Balance balance = new Balance();
    try { balance.withdraw(-10); }
    catch (IllegalArgumentException expected) {}
    System.out.print(balance.amount());
  }
}
```

Rejecting an invalid withdrawal inside the operation protects callers using any interface to the object. The demonstration uses integer units and a single thread. It does not establish financial rounding policy or concurrent atomicity; those are separate requirements that a production balance model must address.

## Advanced

### Behavioral substitution and failure contracts

A subtype should preserve the promises clients rely on. Strengthening preconditions, weakening postconditions or unexpectedly taking ownership of a borrowed resource can break substitution. Consider a read-only repository implemented as a subtype of a mutable repository: throwing UnsupportedOperationException from every write method may expose that the original interface grouped incompatible capabilities.

Separate interfaces by meaningful capability rather than creating one interface per method mechanically. A caller that needs lookup should depend on lookup, while a workflow that needs atomic mutation should use an operation that exposes the relevant business contract. This makes both tests and alternative implementations easier to reason about.

### Equality across hierarchies

Equality should behave as an equivalence relation and remain consistent while its significant state is unchanged. A subclass adding new equality-significant fields can conflict with a superclass that considers only its own fields. Decide whether equality is exact-class-based, interface/value-based, or not appropriate across that hierarchy.

Always keep equals and hashCode compatible: equal objects need equal hashes, while different objects may share a hash. Do not base long-lived hash membership on fields that will later mutate. Generated identifiers in persistence models require particular attention because assigning an ID after insertion into a set can change the equality/hash assumptions.

### Defensive copying and shallow immutability

Copy mutable inputs if the caller must not retain a way to change your state. Copy or expose safe representations of mutable outputs as well. An unmodifiable view prevents writes through that view but can still reflect modifications made through another reference to the backing collection.

A copied collection can still contain shared mutable elements. A record holding a List is not automatically deeply immutable; its component reference is final, but the list and its elements need an ownership policy. State whether a value is a snapshot, a live view, a shared immutable value, or a borrowed handle.

### Initialization and overridable methods

Constructors run before the object is fully initialized for general use. Calling an overridable method from a superclass constructor can dispatch into subclass code before subclass field initialization has finished. That code may observe default values and violate invariants unexpectedly.

Avoid publishing this from construction through listeners, global registries or background tasks. The issue is not only thread safety: even single-threaded callbacks can observe an incomplete object. Prefer a clear construction phase followed by explicit registration/startup when the object is ready.

### Interface evolution and default methods

Default methods can provide behavior in interfaces, but adding one is not free of compatibility considerations. Unrelated inherited defaults with conflicting signatures may require an explicit override. A class method and interface defaults also participate in defined resolution rules rather than arbitrary declaration order.

Keep interface evolution centered on contracts. A default implementation that silently does nothing might preserve compilation while violating an important operational expectation. Document new behavior, verify existing implementations and test consumers that depend on earlier semantics.

### Erasure, bridge methods and runtime identity

Generic erasure can require compiler-generated bridge methods to preserve overriding relationships. Calling a parameterized implementation through a raw reference can bypass useful compile-time checks and fail in a cast performed by a bridge. An unexpected synthetic method in a stack trace is not automatically a framework bug.

Runtime class identity includes the defining class loader as well as the binary name. Two plugins can contain interfaces with identical names yet fail casts if they define separate copies. Share boundary contracts through the intended loader and keep implementation dependencies isolated deliberately.

## Production

### Prefer testable dependency boundaries

A service that constructs its database, clock and remote client internally makes failure cases difficult to test. Inject appropriate collaborators at boundaries that vary. Do not abstract every arithmetic operation; introduce interfaces where substitution, lifecycle or external effects justify them.

Test the advertised behavior with multiple implementations or controlled doubles. A fake repository that always succeeds cannot demonstrate transaction failure handling. A mock that verifies calls without checking resulting invariants can pass while the workflow is wrong. Combine small contract tests with integration tests for real boundary behavior.

### Model ownership of resources

If a method borrows a Writer from its caller, closing it may break later caller operations. If the method opens its own file stream, failing to close it leaks an owned resource. Document who closes resources and whether data is buffered, flushed or retained after the call.

Ownership also applies to callbacks and subscriptions. A long-lived publisher holding a listener can keep its enclosing object reachable. Provide an explicit removal/lifecycle mechanism where appropriate, and test shutdown. Object-oriented relationships have memory and resource consequences beyond the class diagram.

### Diagnose inheritance that resists change

If adding a feature requires subclasses to override methods in a fragile order, inspect whether implementation inheritance is carrying several independent responsibilities. Extract a collaborator for the changing policy and keep invariant-preserving orchestration in one place. This is a reasoned use of composition, not a rule that inheritance is always wrong.

Refactor around observable contracts so existing clients retain their behavior. A class hierarchy may be part of a public API, and changing it can have source or binary compatibility effects. Small internal cleanup and public API redesign need different rollout strategies.

## Exam reasoning

### Resolve the call before predicting the output

Identify whether the member is an instance method, static method or field. Determine overload applicability using compile-time types, then apply runtime overriding only where the language requires it. Access errors, ambiguous calls or incompatible checked exceptions can prevent compilation before any output exists.

### Read the complete invariant

Private fields, final references and record syntax are not interchangeable proofs of immutability. Look for exposed mutable collections, callbacks, subclass hooks and shared elements. A correct answer should explain the specific path by which state can change or why that path is prevented.

### Distinguish Java legality from design correctness

The compiler can accept a subtype that violates a business contract, a globally mutable singleton or an API that closes borrowed resources. Design questions require reasoning about caller expectations. Conversely, a desirable design intention does not make illegal Java syntax compile.

## Cheatsheet

| Concept | Rule or question |
| --- | --- |
| Encapsulation | Do operations preserve invariants, including through returned references? |
| Substitution | Preserve the caller's expected inputs, outcomes and failure behavior |
| Composition | Delegate independent responsibilities without claiming an inappropriate subtype |
| Overloading | Compile-time argument types determine applicability |
| Overriding | Runtime dispatch selects an eligible instance implementation |
| Static/field hiding | Not the same dispatch mechanism as instance overriding |
| Equality | Define meaningful identity and keep the equivalence contract |
| hashCode | Equal values require equal hashes; unequal values may collide |
| Immutability | Consider the entire reachable state and every mutation path |
| Defensive copying | Distinguish snapshots, views and shared mutable elements |
| Constructor safety | Avoid overridable calls and premature publication |
| Interface evolution | Default methods still have resolution and contract implications |
| Bridge methods | Erasure can introduce synthetic dispatch adapters |
| Class-loader identity | Same binary name does not guarantee the same runtime type |
| Resource ownership | Close what you own; respect borrowed lifetimes |
| Dependency boundaries | Abstract genuine variation, not every implementation detail |

## Check yourself

### 1. Polymorphic call

Why does a Payment reference holding a Card invoke Card.label?

**Answer:** The call is a permitted instance method, and runtime overriding dispatch selects the Card implementation. The reference type still controls which calls are available to compile.

### 2. Overload versus override

Why does example O2 print base:child rather than child:child?

**Answer:** pick is overloaded using the compile-time Base argument type, while name is overridden and dispatched using the actual Child object.

### 3. Advanced: an unmodifiable view

A getter returns an unmodifiable view of an internal list, but another method mutates the backing list. Is the returned view an immutable snapshot?

**Answer:** No. It prevents mutation through that view but can reflect backing changes. A snapshot requires the appropriate copy and an element-ownership policy.

### 4. Advanced: subclass equality

A base value compares only an ID while a subtype also compares a region. What contract risk should be reviewed?

**Answer:** Equality can lose symmetry or transitivity across the hierarchy. Choose and document one consistent equality domain rather than independently extending equality rules.

### 5. Advanced: constructor dispatch

A superclass constructor invokes an overridable method implemented in a subclass. Why can that method see an uninitialized subclass field?

**Answer:** Dynamic dispatch can reach the override before subclass initialization has completed. Avoid invoking such hooks during construction.

### 6. Identically named plugin interfaces

Why can a cast fail between two interfaces with the same fully qualified name loaded by different defining class loaders?

**Answer:** They are distinct runtime types. Share the intended API from a common loader instead of packaging independent private copies of the boundary contract.

## Sources

Reviewed 2026-09-25. Baseline: Java SE 17; the bridge-method tutorial explains a mechanism already present in Java 8.

- [JLS 17 classes](https://docs.oracle.com/javase/specs/jls/se17/html/jls-8.html).
- [JLS 17 interfaces](https://docs.oracle.com/javase/specs/jls/se17/html/jls-9.html).
- [JLS 17 execution and initialization](https://docs.oracle.com/javase/specs/jls/se17/html/jls-12.html).
- [JLS 17 expressions and invocation](https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html).
- [Object equality and hashing](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html).
- [Record API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Record.html).
- [Collection views](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Collections.html).
- [Bridge methods](https://docs.oracle.com/javase/tutorial/java/generics/bridgeMethods.html).
- [JVM loading and class identity](https://docs.oracle.com/javase/specs/jvms/se17/html/jvms-5.html).
