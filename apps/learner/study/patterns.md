## Understand

A design pattern names a recurring solution structure. First identify what changes and who should own that change. A pattern adds value when it clarifies a responsibility; using its name does not prove the design fits.

Strategy selects interchangeable behavior, such as a shipping-price algorithm. Factory Method delegates creation to an overridable operation; Abstract Factory supplies a family of compatible products. Builder separates staged construction from the finished object and should enforce required invariants before returning it.

Adapter translates an incompatible interface. Decorator wraps a compatible interface to add behavior. Proxy controls access to another object, which may be remote. Facade presents a simpler entry point to a subsystem. These structures can look similar while having different purposes.

## Apply

A JSON exporter and an XML exporter each need a matching parser and renderer. Independent configuration of both can create an invalid pair. A family factory groups their creation:

```java
interface FormatFactory {
    Parser parser();
    Renderer renderer();
}
```

This sketch assumes application-defined Parser and Renderer interfaces. Selecting one factory establishes a compatibility boundary; validate the external configuration selecting it.

A remote order proxy with ten getters called for 100 orders can cause 1,000 requests. Introduce a bounded bulk-summary operation. Caching proxy objects or naming the proxy "local" does not remove remote round trips.

## Cheatsheet

| Pattern | Choose it when |
| --- | --- |
| Observer | Publishers should notify subscribers without knowing their concrete types |
| Command | An action needs queuing, logging or undo; capture the receiver and previous state |
| Visitor | Operations vary over a relatively stable element hierarchy |
| Composite | Individual and grouped objects should share a uniform operation |
| Flyweight | Share intrinsic state; pass position/user/context as extrinsic state |
| Singleton | One instance per defined scope; not automatically thread-safe or cluster-wide |
| Circuit breaker | Stop repeated calls to an unhealthy dependency, then probe recovery |

## Check yourself

Cached glyphs share font and character, but storing a document's x/y position inside each cached glyph corrupts other documents. What should move?

**Answer:** Keep font/character drawing information shared; pass each use's position separately. The position belongs to the caller's context.

## Sources

[Oracle enterprise pattern catalog](https://www.oracle.com/java/technologies/core-j2ee-patterns.html) · [Undoable edit contract](https://docs.oracle.com/javase/8/docs/api/javax/swing/undo/AbstractUndoableEdit.html) · [Circuit breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)
