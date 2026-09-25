## Understand

Choose a collection by its contract before its implementation. A `List` preserves positions and allows duplicates. A `Set` represents uniqueness. A `Map` maps keys to values. A `Queue` exposes work waiting for processing; a `Deque` supports both ends and often replaces legacy `Stack`.

`ArrayList` supports constant-time indexed access; insertion in its middle shifts elements. `HashMap` and `HashSet` use equality plus hash codes and do not guarantee iteration order. `LinkedHashMap` preserves insertion order by default. `TreeMap` and `TreeSet` use ordering comparisons. Objects that compare as zero occupy one logical sorted-key position even if `equals` disagrees.

Generics let the compiler check element types. `List<Integer>` is not a subtype of `List<Number>`. A producer often uses `? extends T`; a consumer often uses `? super T`. This is the PECS reminder, not permission to mutate every wildcard collection.

## Apply

An employee set sorted only by salary drops distinct employees with equal salaries. Add a stable identity tie-breaker:

```java
Comparator<Employee> order = Comparator
    .comparingInt(Employee::salary)
    .thenComparing(Employee::id);
Set<Employee> employees = new TreeSet<>(order);
```

This fragment assumes `Employee` exposes those accessors and imports `java.util` types. Make the ordering match the intended identity contract. Changing `hashCode` cannot repair a TreeSet comparator.

For grouping frequencies, `Collectors.toMap(keyMapper, valueMapper, mergeFunction)` resolves duplicate keys explicitly. The two-argument overload instead rejects duplicate keys. Decide whether to sum, retain or reject duplicates from the business rule.

## Cheatsheet

| Operation | Distinction |
| --- | --- |
| `get(key)` returns null | Absent key or mapped null; use `containsKey` when needed |
| `remove(1)` on `List<Integer>` | Removes index 1; `remove(Integer.valueOf(1))` removes a value |
| `poll` / `remove` | Both dequeue; empty `poll` returns null, empty `remove` throws |
| `Arrays.asList` | Fixed-size view backed by the array, not an ordinary resizable list |
| `List.of` | Unmodifiable, rejects nulls; contained objects may still mutate |
| Hash keys | Do not mutate fields involved in equality/hash while used as keys |

A fail-fast iterator is a debugging aid, not a concurrency protocol. Use a suitable concurrent collection or synchronize the complete compound operation.

## Check yourself

Can you add an `Integer` to a `List<? extends Number>`?

**Answer:** Not safely: the actual list might contain only `Double`. You can read elements as `Number`. A `List<? super Integer>` accepts integers but reads as `Object`.

## Sources

[Collections framework](https://dev.java/learn/api/collections-framework/) · [Wildcards](https://docs.oracle.com/javase/tutorial/java/generics/wildcards.html) · [TreeSet contract](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/TreeSet.html)
