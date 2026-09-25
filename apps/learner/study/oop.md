## Understand

An object combines state and behavior. Encapsulation protects invariants: a `BankAccount` should reject an invalid withdrawal inside its operation, rather than trust every caller to check its balance. Constructors establish valid initial state; private fields alone do not guarantee good encapsulation if getters expose mutable internals.

Inheritance models a substitutable subtype. Prefer composition when a class merely uses another service. An interface defines a contract; an abstract class can share state and implementation. Java supports one class superclass and multiple interfaces. Overriding supplies subtype behavior for an instance method; overloading supplies another parameter list and is resolved using compile-time types.

`public` is broadly accessible, package access stays within the package, and `private` stays within the declaring class and its nest. `protected` also supports subclass access, with additional restrictions across packages. `final` prevents reassignment, overriding or inheritance depending on where it appears; a final reference does not make its object immutable.

## Apply

This complete Java 17 program prints `card`:

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

The reference type determines what calls compile; the runtime object determines the overriding implementation. Static methods and fields do not use this same instance dispatch. Avoid calling overridable methods from a constructor: subclass initialization may not have finished.

## Cheatsheet

| Decision | Rule |
| --- | --- |
| Equality | Override `equals` and `hashCode` together; equal objects need equal hashes |
| Immutability | Validate construction, prevent mutation, copy mutable inputs and outputs |
| Substitution | Subtypes must honor the advertised contract, including failure behavior |
| Dependency inversion | Depend on an abstraction at the boundary that varies |
| Interface segregation | Give clients the operations they actually need |
| Resource ownership | A borrowed Writer should not be closed if its caller still needs it |
| Runtime type | Identity includes the binary name and defining class loader |

Generic erasure may insert bridge methods. Calling a `Sink<String>` through a raw `Sink` with an integer can compile with a warning and fail in the bridge's cast. Raw types remove useful checks rather than make all values interchangeable.

## Check yourself

Two plugin interfaces have the same fully qualified name but different defining class loaders. Why can a cast fail?

**Answer:** They are different runtime types. Share the interface from a common parent loader instead of defining private copies in both host and plugin.

## Sources

[Classes and objects](https://dev.java/learn/classes-objects/) · [Inheritance](https://dev.java/learn/inheritance/) · [Bridge methods](https://docs.oracle.com/javase/tutorial/java/generics/bridgeMethods.html)
