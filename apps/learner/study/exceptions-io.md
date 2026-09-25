## Understand

Checked exceptions must be caught or declared; `RuntimeException` and `Error` subclasses are unchecked. Catch at a boundary that can recover, translate or report meaningfully. Preserve the cause when translating. A broad catch that reports success hides the original failure.

Try-with-resources closes `AutoCloseable` resources in reverse declaration order. If the body throws and close also throws, the body exception remains primary and the close exception is suppressed. A return or throw in `finally` can hide an earlier result; avoid it.

Use explicit character encodings and bounded I/O. `Path` identifies a location; `Files` provides operations. Close streams you own, and define who closes borrowed streams. Never assume an entire upload fits memory.

`BigDecimal` supports decimal arithmetic; construct money from decimal strings, define scale and rounding, and apply the business rule at the correct boundary. `new BigDecimal(0.1)` preserves the binary floating-point approximation.

## Apply

This fragment reads UTF-8 lines while guaranteeing reader closure:

```java
try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    for (String line; (line = reader.readLine()) != null; ) {
        process(line);
    }
}
```

The enclosing operation must handle or declare `IOException`. Here `path` and `process` are application-specific. Validate paths and input sizes separately; automatic closure does not validate data.

For an appointment at 09:00 tomorrow in a user's zone, add a calendar day to a `ZonedDateTime`. A duration of 24 hours means elapsed time and may move the local clock across daylight-saving transitions. Persist the instant and enough zone/business context for the operation.

## Cheatsheet

| Need | Type / approach |
| --- | --- |
| Timestamp on a timeline | `Instant` |
| Date without timezone | `LocalDate` |
| Local date and time | `LocalDateTime`; not an unambiguous global timestamp |
| Regional timezone rules | `ZonedDateTime` with `ZoneId` |
| Elapsed time / calendar amount | `Duration` / `Period` |
| Precise decimal division | Specify scale or `MathContext` and rounding as required |
| Exception diagnostics | Cause chain and `getSuppressed()` |

## Check yourself

A try block throws `IllegalStateException`; closing its resource throws `IOException`. Which exception reaches the catch?

**Answer:** The `IllegalStateException`, with the close exception in its suppressed list. This preserves the original failure while retaining cleanup diagnostics.

## Sources

[Exception handling](https://dev.java/learn/exceptions/) · [Date/time](https://dev.java/learn/date-time/) · [BigDecimal](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/math/BigDecimal.html)
