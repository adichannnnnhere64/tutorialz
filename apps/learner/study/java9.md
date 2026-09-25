## Understand

Java 9 added the module system (JPMS), JShell, collection factories, private interface methods, Flow and stream enhancements. A named module declares dependencies with `requires`, exposes public API packages with `exports`, and permits deep reflection with `opens`. Exporting and opening solve different access problems.

`List.of`, `Set.of` and `Map.of` create unmodifiable collections and reject nulls. Their elements may still refer to mutable objects. Private interface helpers can support default methods but are not inherited by implementers.

Flow models a publisher/subscriber relationship with explicit demand. `request(n)` adds to outstanding demand; each delivered item consumes one unit. Cancellation is best-effort and does not promise an immediate terminal callback.

## Apply

This complete Java 9 program prints `2,4`:

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

For this ordered stream, `takeWhile` retains the matching prefix. `filter` would also retain 6; `dropWhile` would keep 1 and 6. Unordered streams have different permitted behavior, so include ordering assumptions when reasoning about a result.

## Cheatsheet

| Feature | Remember |
| --- | --- |
| `Optional.stream()` | Zero or one stream element; useful with `flatMap` |
| `Stream.iterate(seed, predicate, next)` | Bounded generation while the predicate holds |
| JShell | Try snippets interactively; not a replacement for a project build |
| `jdeps --jdk-internals` | Finds bytecode dependencies on internal JDK APIs |
| `javac --release 9` | Restricts language, bytecode and supported platform APIs to Java 9 |
| Multi-release JAR | `Multi-Release: true`; select highest eligible `META-INF/versions/N` entry |
| `--add-opens` | Temporary reflective-access workaround; prefer supported APIs |

Strong encapsulation tightened in later JDKs. A migration must check runtime dependencies as well as successful compilation. `-source` and `-target` alone do not prevent linking against newer APIs on the build JDK.

## Check yourself

A subscriber requests 2 items, receives 1, then requests 3. How much outstanding demand remains?

**Answer:** Four: `2 - 1 + 3`. The later request adds demand rather than replacing it.

## Sources

[Java 9 Stream](https://docs.oracle.com/javase/9/docs/api/java/util/stream/Stream.html) · [Flow subscription](https://docs.oracle.com/javase/9/docs/api/java/util/concurrent/Flow.Subscription.html) · [JAR specification](https://docs.oracle.com/javase/9/docs/specs/jar/jar.html)
