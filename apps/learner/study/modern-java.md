## Understand

For these exams, Java 17 is the usual baseline and Java 21 is used where named. Distinguish the language/API version from a framework's minimum supported JDK. A feature being useful today does not mean it was introduced in the most recent release.

Records describe data carriers and generate component accessors, equality, hashing and string representation. They are shallowly immutable: a record containing a mutable list still exposes mutable state unless the constructor copies it. Sealed types restrict permitted implementations and help model a known set of domain alternatives.

Java 17 supports pattern matching for `instanceof`. The pattern variable exists only where control flow establishes a successful match. `value instanceof String s && s.isEmpty()` is valid; using `s` on the right of `||` is not, because that operand can run after a failed match.

## Apply

Java 17 data carrier with a defensive copy:

```java
record Basket(java.util.List<String> items) {
    Basket {
        items = java.util.List.copyOf(items);
    }
}
```

The copy creates an unmodifiable list snapshot and rejects null elements. Since strings are immutable, callers cannot mutate a string through the list. If the elements were mutable objects, copying the list alone would not copy those objects.

Java 21 virtual threads make large numbers of blocking I/O tasks practical. They do not make CPU work faster or increase a database's connection count. With 40 database connections, thousands of virtual threads still compete for those 40 connections; bound admission and measure waiting time.

## Cheatsheet

| Feature | Version / boundary |
| --- | --- |
| Records | Finalized in Java 16; no arbitrary additional instance fields |
| Sealed classes | Finalized in Java 17; permitted direct subtypes declare an appropriate modifier |
| `instanceof` patterns | Finalized in Java 16; scope follows successful matching |
| Virtual threads | Finalized in Java 21; useful for blocking workloads |
| Sequenced collections | Java 21 first/last/reversed operations |
| Reversed collection view | Usually backed by the original; not an independent snapshot |
| Preview features | Must be explicitly enabled and tied to a specific release |

## Check yourself

An ArrayList contains A, B, C. On Java 21, you obtain its reversed view, then append D to the original. What does the view show?

**Answer:** D, C, B, A. The view reflects changes in the backing list. It does not freeze the original contents.

## Sources

[Records](https://dev.java/learn/records/) · [Sealed classes](https://dev.java/learn/inheritance/sealed-classes-and-interfaces/) · [JEP 444](https://openjdk.org/jeps/444) · [SequencedCollection](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/SequencedCollection.html)
