## Understand

Java 8 introduced lambdas, method references, default/static interface methods, streams, Optional and the modern date/time API. A lambda implements a functional interface's single abstract method. `Predicate<T>` tests, `Function<T,R>` transforms, `Consumer<T>` consumes, and `Supplier<T>` supplies. Captured local variables must be final or effectively final; captured objects may still be mutable.

A stream describes a pipeline, not a container. Intermediate operations are generally lazy; a terminal operation triggers evaluation. Streams are single-use. Distinguish `map` (one transformed result per input) from `flatMap` (flatten nested streams). Side effects, shared mutation and parallel ordering need explicit thought.

Optional describes a present or absent value. Prefer composition to unchecked `get()`. `orElse(expensive())` evaluates its argument eagerly; `orElseGet(() -> expensive())` defers fallback execution until needed.

## Apply

This complete Java 8 program prints `2:10`:

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

The filter retains 2 and 3, mapping produces 4 and 6, and summing produces 10. `Collectors.toList()` does not promise a particular implementation or mutability contract; use `toCollection` when that matters.

## Cheatsheet

| API | Key distinction |
| --- | --- |
| `filter` / `map` | Retain elements / transform values |
| `reduce` | Associative combination; identity must fit the operation |
| `collect` | Mutable reduction with supplier/accumulator/combiner semantics |
| `findFirst` / `findAny` | Encounter-order first / any matching result |
| `forEachOrdered` | Preserves encounter order when defined |
| Interface default method | Inherited behavior; conflicting unrelated defaults need resolution |
| Method reference | `Type::staticMethod`, `instance::method`, `Type::new` |

`List.of`, `Optional.stream` and `takeWhile` are Java 9 additions. `Stream.toList()` arrived later, in Java 16; do not use it in Java 8-targeted code.

## Check yourself

Why is adding elements to a shared ArrayList from a parallel `forEach` unsafe?

**Answer:** The list is not protected against concurrent structural writes. Use the stream's collection operation so partial results can be combined according to its contract.

## Sources

[Lambdas](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) · [Java 8 streams](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html) · [Optional](https://docs.oracle.com/javase/8/docs/api/java/util/Optional.html)
