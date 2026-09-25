## Understand

### Scope and learning objectives

This chapter targets Java 17 and covers exception flow, resource ownership, byte/text I/O, decimal arithmetic and time. These topics share a practical concern: translating external data and failures into a dependable application model. You should be able to explain which exception escapes, who closes a resource, which bytes are valid text, and which representation matches a monetary or time requirement.

An exception is control flow plus diagnostic information. Checked exceptions participate in compile-time handling rules; unchecked exceptions generally represent failures not subject to those same declaration requirements. Choosing between them is an API design decision, not proof that one category is always recoverable and the other never is.

### Ownership before syntax

A method that opens a file normally owns the handle it created. A method receiving a caller-owned stream may only borrow it. Try-with-resources is appropriate for owned AutoCloseable resources, but wrapping a borrowed stream and closing the wrapper can close the underlying resource too. State ownership in the contract instead of relying on a caller to guess.

Memory and operating-system resources have different lifetimes. Garbage collection does not provide a timely release policy for file descriptors, sockets or database connections. A short-lived Java reference can still correspond to a scarce external resource that needs deterministic cleanup.

### Bytes, characters, decimal values and dates

Bytes are not text until decoded with a character encoding. A Reader/Writer operates on character data, while InputStream/OutputStream works with bytes. Select the encoding from the protocol or file format; relying on an unspecified environment default makes behavior harder to reproduce.

Binary floating-point is valuable for many numerical tasks but does not exactly represent every decimal fraction. Monetary calculations need explicit units, scale and rounding rules. Time likewise has multiple representations: an Instant identifies a point on a timeline, a LocalDate represents a calendar date, and a LocalDateTime alone does not identify an instant without zone/offset rules.

## Apply

### Example E1: primary and suppressed exceptions

Complete Java 17 program; expected output: `body:close`.

```java
class Main {
  static final class Resource implements AutoCloseable {
    public void close() throws Exception { throw new Exception("close"); }
  }
  public static void main(String[] args) {
    try (Resource resource = new Resource()) {
      throw new Exception("body");
    } catch (Exception failure) {
      System.out.print(failure.getMessage() + ":" +
          failure.getSuppressed()[0].getMessage());
    }
  }
}
```

The body failure remains primary while the close failure is recorded as suppressed. With multiple resources, successful initializations are closed in reverse order. This differs from a poorly written finally block whose own abrupt completion can replace the earlier failure without automatically recording it as a suppressed exception.

### Example E2: ByteBuffer state changes

Complete Java 17 program; expected output: `42:0`.

```java
import java.nio.*;
class Main {
  public static void main(String[] args) {
    ByteBuffer buffer = ByteBuffer.allocate(8);
    buffer.putInt(42);
    buffer.flip();
    int value = buffer.getInt();
    System.out.print(value + ":" + buffer.remaining());
  }
}
```

After writing four bytes, flip makes those written bytes the readable region by changing position and limit. Reading the integer consumes that region. Clear resets bookkeeping for another write; it does not promise to erase the old contents. Byte order is also part of a binary-format contract and must match the protocol.

### Example E3: decimal equality and numerical comparison

Complete Java 17 program; expected output: `false:0`.

```java
import java.math.*;
class Main {
  public static void main(String[] args) {
    BigDecimal first = new BigDecimal("2.0");
    BigDecimal second = new BigDecimal("2.00");
    System.out.print(first.equals(second) + ":" + first.compareTo(second));
  }
}
```

BigDecimal.equals includes scale, while compareTo compares numerical value. This distinction affects sets, maps and domain equality. Decide whether your application treats scale as meaningful before normalizing values or selecting an ordering-based collection.

### Example E4: a local time in a daylight-saving gap

Complete Java 17 program; expected output: `03:30`.

```java
import java.time.*;
class Main {
  public static void main(String[] args) {
    LocalDateTime local = LocalDateTime.of(2024, 3, 10, 2, 30);
    ZonedDateTime resolved = local.atZone(ZoneId.of("America/New_York"));
    System.out.print(resolved.toLocalTime());
  }
}
```

The local time lies in a DST gap under the zone's rules and the conversion adjusts it forward. That default resolution may not be the right business policy for a booking or scheduled payment. Validate and explain how your application handles missing or repeated local times instead of assuming every local clock reading maps to exactly one instant.

## Advanced

### Exception translation and preserved causes

Translate failures at an abstraction boundary when the caller needs a different vocabulary, such as an import failure rather than a vendor-specific parsing detail. Preserve the underlying cause and relevant safe context. Throwing a new exception containing only the old message loses stack and type information needed for diagnosis.

Do not catch Exception merely to log and return a success-shaped default. That can turn a failed database read into an empty result that callers mistake for authoritative absence. Distinguish an expected “not found” outcome from a failed lookup. Also avoid logging the same failure at every layer; choose the boundary responsible for reporting the operation's outcome.

### Cleanup, suppression and partial acquisition

If resource acquisition fails after an earlier resource was successfully acquired, the earlier owned resources still need cleanup. Try-with-resources handles this ordering for its resource declarations. A close failure does not prevent later cleanup attempts for the other resources under the language's specified transformation.

Inspect suppressed exceptions when the primary failure alone does not explain the incident. A failed flush during close can mean output was incomplete even if the body looked successful. Do not return from finally to force a preferred result; doing so can hide failures and make callers believe a failed operation completed normally.

### NIO buffers and partial operations

A channel operation need not transfer an entire application message in one call. Reads can return a partial count; nonblocking reads can return zero; end of stream has its own signal. Writes can also be partial. Track buffer position/limit and loop according to the channel's blocking/readiness contract.

Compact retains unread data while preparing space for more input, whereas clear discards the current read/write bookkeeping. Neither is a data-format parser. Frame messages explicitly with lengths, delimiters or a protocol definition, and apply size limits before allocating buffers from untrusted length fields.

### Charset decoding and malformed input

A multibyte character can be split across network reads. Decoding each arbitrary byte chunk independently can corrupt text or report spurious errors. Use a streaming decoder that retains the required state and handle underflow, overflow and end-of-input correctly.

Choose a malformed/unmappable-input policy deliberately: report, replace or another supported action. Replacing invalid bytes might be acceptable for a display preview but inappropriate when verifying signed data or importing identifiers. Decode and canonicalize at defined boundaries so security checks and business logic agree about the actual text.

### Decimal precision, scale and rounding

Constructing BigDecimal from a decimal string preserves the intended decimal value; constructing from a double can preserve the binary floating-point approximation instead. Division may require a rounding rule when the decimal expansion does not terminate. Select MathContext or scale/RoundingMode according to the business calculation, not merely to silence ArithmeticException.

Rounding at every intermediate step can produce a different total from rounding at a specified settlement boundary. Define how taxes, discounts, allocation remainders and negative amounts are treated. Represent currency explicitly when different currencies use different minor-unit conventions, and never infer all currencies use exactly two decimal places.

### Time zones, DST and reproducible clocks

A zone ID includes rules that can change over history and with time-zone database updates. An offset is a specific difference from UTC, not a complete future scheduling rule. Store enough information to preserve the business meaning: an event instant and a recurring local appointment are different requirements.

Duration measures time-based amounts, while Period expresses date-based amounts. Adding one calendar day across a DST transition need not equal adding exactly 24 hours. Inject a Clock into time-dependent code so tests can reproduce boundaries without waiting or changing the machine clock. DateTimeFormatter is immutable/thread-safe; older mutable formatting utilities need different concurrency treatment.

## Production

### Make file replacement and durability explicit

Writing a file successfully is not always the same as atomically replacing the old version or ensuring persistence after power loss. A safe update often writes a temporary file in an appropriate location, closes/flushes it, then performs a supported move with explicit replacement policy. Atomic-move support depends on the filesystem and operation.

Decide what to do if atomic replacement is unavailable rather than silently weakening a critical guarantee. Preserve recoverable originals when practical. Validate paths against traversal and unexpected symbolic-link behavior when operating on untrusted names, and use least-privilege directories and permissions.

### Bound imports and exports

Do not load an arbitrarily large file into memory solely because a convenience method returns a list of lines. Stream bounded records when size demands it, while ensuring the stream is closed. Enforce maximum record length, number of records and decompressed size for compressed input.

An import may fail halfway through. Define whether it is all-or-nothing, chunked with resumable progress, or a best-effort operation with per-record results. Preserve enough context to identify rejected records without logging secrets. Resource cleanup does not itself roll back previously committed business changes.

### Test failure paths with realistic boundaries

Test a close failure, truncated multibyte input, a short channel read, a nonterminating decimal division, a DST gap and a DST overlap. These cases reveal ownership and representation assumptions that ordinary examples miss. Assertions should check the intended outcome and retained diagnostic context, not just that some exception occurred.

Separate portability guarantees from environment behavior. Filesystem operations, default encodings and time-zone rules can vary. State the environment when testing those details and use explicit configuration where the protocol permits it.

## Exam reasoning

### Trace normal and abrupt completion separately

Determine whether a try body returns, throws or completes normally, then apply resource-closing and catch/finally behavior. A return expression can be evaluated before cleanup, but cleanup can still change how the statement completes. Distinguish the exception's cause from its suppressed exceptions; they describe different relationships.

### Identify what a buffer operation changes

Flip, clear, rewind and compact manipulate buffer state differently. Start with capacity, position and limit, then trace each operation. Do not assume clear zeroes sensitive data or that one channel write sends everything remaining.

### Ask which equality or time model is used

BigDecimal.equals and compareTo can disagree about numerical equivalents with different scales. LocalDateTime is not an instant. A period of one day is not universally 24 elapsed hours. The correct answer depends on the actual API and representation, not the everyday meaning of “same amount” or “tomorrow.”

## Cheatsheet

| Concept | Rule or diagnostic |
| --- | --- |
| Exception translation | Preserve cause and safe operation context |
| Suppressed exception | Additional failure during cleanup, distinct from cause |
| try-with-resources | Close successfully acquired owned resources in reverse order |
| finally | Abrupt completion can replace an earlier result/failure |
| Ownership | Closing a wrapper can close a borrowed underlying stream |
| ByteBuffer.flip | Prepare written data for reading |
| ByteBuffer.clear | Reset bookkeeping, not guaranteed erasure |
| ByteBuffer.compact | Preserve unread bytes and make write space |
| Partial I/O | Loop according to count, EOF and readiness contracts |
| Charset decoding | Retain state across split multibyte sequences |
| Malformed input | Select reporting/replacement policy deliberately |
| BigDecimal precision | Decimal representation and rounding need a domain rule |
| Scale equality | equals differs from numerical compareTo |
| Instant / local time | Timeline point versus calendar representation |
| Zone / offset | Rule set versus a particular UTC difference |
| DST gap/overlap | Local time can map to zero or two offsets |
| Duration / Period | Elapsed-time amount versus date-based amount |
| Clock | Inject time for deterministic tests |
| File replacement | Completion, atomicity and durability are separate guarantees |

## Check yourself

### 1. Two failures

A try-with-resources body throws and its resource close also throws. Which failure is normally primary?

**Answer:** The body failure remains primary and the close failure is attached as suppressed, subject to the language's defined resource-handling behavior.

### 2. Buffer after flip

Why does example E2 report no remaining bytes after reading one integer from an eight-byte-capacity buffer?

**Answer:** Flip set the readable limit to the four bytes that were written. Capacity remains eight, but remaining depends on the current position and limit.

### 3. Advanced: split UTF-8 sequence

Why can decoding each network chunk separately corrupt text even when the complete byte stream is valid?

**Answer:** A multibyte character can cross chunk boundaries. A stateful decoder must retain incomplete input until the next chunk arrives and apply the intended error policy.

### 4. Advanced: decimal comparison

Can two BigDecimal values compare numerically equal while equals returns false?

**Answer:** Yes. equals includes scale, while compareTo can report zero for numerically equal values with different scales. Choose domain equality and collection semantics deliberately.

### 5. Advanced: tomorrow versus 24 hours

Why can adding one calendar day to a zoned time differ from adding 24 elapsed hours?

**Answer:** DST and other zone transitions can change the day's elapsed length. Period-like calendar arithmetic and Duration-like timeline arithmetic model different requirements.

### 6. Borrowed writer

A helper receives a Writer owned by its caller. Must the helper always close it in try-with-resources?

**Answer:** No. Follow the ownership contract. Closing a borrowed writer can invalidate later caller operations; the component that owns the lifetime should arrange closure.

## Sources

Reviewed 2026-09-25. Baseline: Java SE 17; DST example uses the historical America/New_York transition on 2024-03-10.

- [JLS try-with-resources semantics](https://docs.oracle.com/javase/specs/jls/se17/html/jls-14.html).
- [Throwable and suppressed exceptions](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Throwable.html).
- [AutoCloseable](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/AutoCloseable.html).
- [ByteBuffer](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/ByteBuffer.html).
- [CharsetDecoder](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/charset/CharsetDecoder.html).
- [Files](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/file/Files.html).
- [BigDecimal](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/math/BigDecimal.html).
- [ZonedDateTime](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/ZonedDateTime.html).
- [Clock](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/Clock.html).
- [DateTimeFormatter](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/format/DateTimeFormatter.html).
