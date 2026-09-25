## Understand

### Values, variables and the learning goal

The baseline is Java 17 unless an example states another release. Learn to distinguish compile-time types, runtime values and the order in which expressions execute. These distinctions explain many apparently surprising results without requiring memorization of isolated tricks. You should finish this chapter able to trace an expression, explain a failed conversion, and diagnose a class-initialization or null-unboxing problem.

Primitive variables contain primitive values. Reference variables contain references or null; the object they identify is a separate entity. Assigning a reference copies the reference, not the object. Two variables can consequently refer to the same mutable array. Java passes every method argument by value, including reference values: a method can mutate a shared object, but assigning a new reference to its parameter does not reassign the caller's variable.

### Primitive types and definite assignment

The integral types byte, short, int and long have 8, 16, 32 and 64 bits respectively. A char is a 16-bit UTF-16 code unit, not necessarily a complete Unicode character. Float and double use binary floating-point representations. Boolean has true and false values; the language does not define a universal one-bit storage layout for every boolean field or array.

Fields and array elements receive default values. Local variables must be definitely assigned before they are read. A variable can therefore be in scope without being legal to read on every control-flow path. Distinguish a compilation error caused by definite assignment from a runtime null dereference caused by a field's default value.

### Control flow, methods and arrays

A for loop performs initialization once, then checks its condition before each iteration, executes its body and performs its update. Continue proceeds to the next iteration; for a for loop that includes the update step. Break exits its selected loop or switch. Braces and labels determine scope and target, so indenting code differently does not change its meaning.

Arrays have fixed length and zero-based indexing. The array's length field differs from String.length() and Collection.size(). An enhanced-for loop copies each element value into its loop variable. Reassigning that loop variable does not replace the element stored in the array, although mutating an object reached through a copied reference can affect the same object.

## Apply

### Example C1: integer division and promotion

Complete Java 17 program; expected output: `2:2.5:10`.

```java
class Main {
  public static void main(String[] args) {
    int[] scores = {4, 6};
    int total = 0;
    for (int score : scores) total += score;
    System.out.print((5 / 2) + ":" + (5 / 2.0) + ":" + total);
  }
}
```

The first division uses integral operands and truncates toward zero. The second has a double operand and uses floating-point arithmetic. Converting the already-computed result of 5 / 2 to double would produce 2.0, not restore the discarded fraction. Conversion must happen before the operation whose precision you intend to change.

### Example C2: overload resolution before boxing

Complete Java 17 program; expected output: `long`.

```java
class Main {
  static String choose(long value) { return "long"; }
  static String choose(Integer value) { return "Integer"; }
  public static void main(String[] args) {
    System.out.print(choose(1));
  }
}
```

The literal has type int. The applicable strict-invocation phase finds widening to long before considering a phase that allows boxing. Return types do not distinguish these overloads. If the argument expression were already an Integer reference, the applicability analysis would differ. Start with the expression's compile-time type rather than the apparent size of its value.

### Example C3: superclass and subclass initialization

Complete Java 17 program; expected output: `P:C:7`.

```java
class Main {
  static class Parent {
    static { System.out.print("P:"); }
  }
  static class Child extends Parent {
    static { System.out.print("C:"); }
    static int value = 7;
  }
  public static void main(String[] args) {
    System.out.print(Child.value);
  }
}
```

Reading the nonconstant static field triggers initialization of its declaring class. The superclass is initialized before the subclass. Within Child, the static block runs before the following field initializer. Do not generalize this exact trace to reading a compile-time constant or to constructing an array of Child references; those operations have different initialization rules.

### Example C4: a nullable wrapper becomes an exception

Complete Java 17 program; expected output: `missing`.

```java
class Main {
  public static void main(String[] args) {
    Integer count = null;
    try {
      int next = count + 1;
      System.out.print(next);
    } catch (NullPointerException missing) {
      System.out.print("missing");
    }
  }
}
```

The arithmetic operation requires unboxing. The reference is null, so failure occurs before addition. The catch block demonstrates the result; production code should normally represent missing data deliberately rather than use NullPointerException as an expected branch.

## Advanced

### Conversions, overflow and numeric intent

Widening does not always mean every original value can be represented exactly: converting sufficiently large integral values to floating point can lose precision. Narrowing can discard information. Arithmetic on small integral types commonly promotes operands to int, so assigning a computed result back to byte or short can require an explicit conversion.

Integer overflow does not ordinarily throw an exception. If overflow is invalid for the use case, use checked operations such as Math.addExact or a suitable larger/arbitrary-precision representation. For money, choose a decimal model and rounding policy rather than assuming double is exact because a printed number looks reasonable. The exceptions and dates chapter develops that boundary further.

### Boxing, identity and evaluation order

A wrapper object has reference identity and a represented value. The equality operator on two wrapper references can compare identity, which is not a sound general substitute for value equality. Some boxing results are reused according to specified or implementation-specific ranges; do not build application logic around observing a larger cache on one runtime.

Java evaluates operands in a defined order, but operator precedence determines the expression tree. Short-circuit operators can skip evaluation of the right operand. Their non-short-circuit boolean counterparts evaluate it as well. Keep side effects out of complicated expressions where possible; code that technically has a defined answer can still be unnecessarily hard to maintain.

### String equality, immutability and Unicode

Strings are immutable, but a variable holding a string reference can be reassigned. Use equals for content comparison and Objects.equals when either reference may be null. The == operator answers an identity question. Interning can make some equal strings share identity, but it does not change the meaning of either operator.

String.length counts UTF-16 code units. A supplementary code point can occupy two units, and a user-perceived grapheme may contain several code points. Choose the right boundary for truncation, cursor movement and validation. Cutting at an arbitrary code-unit position can split a surrogate pair. Encoding text into bytes is a separate operation requiring a charset.

### Class loading, linking and initialization

Loading obtains a class representation; linking includes verification, preparation and resolution; initialization executes the applicable static initialization. These phases are not synonyms. Resolution may occur at different permitted times, so a robust explanation should focus on observable guarantees rather than claim one universal internal loading schedule.

Active use can trigger initialization. Reading a compile-time constant can behave differently because its value may be compiled into a caller. Static initialization failure can leave a class unusable for later attempts through the same loader. Avoid performing fragile remote calls or complex cyclic service wiring in static initializers; those operations make startup failures difficult to recover from and diagnose.

### Reflection and module boundaries

Reflection exposes runtime metadata and selected operations, but it does not erase access-control or module rules. A public class in an unexported package is not automatically an accessible public API to every named module. Deep reflective access may require an appropriate opens relationship; exporting and opening are distinct operations.

When a library fails after a JDK upgrade, inspect the exception and the module/package involved. Do not scatter broad add-opens flags across production merely to silence the first failure. Prefer supported APIs and compatible library versions, and treat temporary reflective-access flags as explicit migration debt with a removal plan.

## Production

### Diagnose malformed input at the boundary

Parsing text can fail even when the destination variable has the correct type. Integer.parseInt rejects invalid formats and out-of-range values. Define accepted whitespace, signs, locale and units rather than letting every caller invent a slightly different parser. Return a useful validation error without exposing internal stack traces to clients.

Scanner mixes token-oriented and line-oriented operations. After nextInt, a following nextLine can consume the remainder of the current line rather than the next logical record. Choose one input model or deliberately consume separators. In service code, also bound input size so a seemingly harmless text operation cannot allocate unbounded memory.

### Avoid accidental allocation and retention

Repeated string concatenation in a large loop can create unnecessary intermediate work; use an appropriate StringBuilder when the task is incremental construction. That does not mean every use of + is inefficient: compilers and runtimes can optimize ordinary expressions. Measure a representative workload rather than apply blanket rules based on source syntax alone.

A long-lived collection, callback or static field can retain objects after the business operation has ended. Garbage collection reclaims unreachable objects, not objects you simply intended to stop using. Diagnose retention paths with suitable tools rather than assuming increasing heap size fixes every memory problem.

### Make errors reproducible

Record the input shape, runtime version, flags and relevant classpath/module path when reproducing a failure. A class-loading conflict, numeric overflow and null-unboxing failure may all surface far from their original cause. Write the smallest test that preserves the relevant mechanism, then add a regression test around the actual business boundary.

Do not print secrets or full customer payloads into logs to reproduce an issue. A minimized synthetic input can demonstrate the language behavior without distributing sensitive data. Distinguish documented language behavior from results that depend on a particular JDK implementation, locale or environment.

## Exam reasoning

### Work in three passes

First check whether the code compiles: scope, definite assignment, access, overload applicability and checked exceptions can prevent execution entirely. Next evaluate expression types and operator order. Finally trace runtime values, initialization and dynamic dispatch. A plausible output is irrelevant if the code is rejected before it can run.

### Watch identity, content and mutation

Ask what is being compared or changed. Reassigning a parameter differs from mutating its referenced object. Comparing strings with == differs from comparing content. A final reference cannot be reassigned but may still reach a mutable object. A local copy of an array element is not the same storage location as the array slot.

### Apply the stated Java version

The language and API surface change across releases. A snippet that uses a Java 17 feature is not a valid Java 8 answer merely because its algorithm is simple. Compilation with --release checks both language/bytecode targeting and supported platform API availability more reliably than source and target flags alone.

## Cheatsheet

| Concept | Rule or diagnostic |
| --- | --- |
| Primitive/reference values | Reference assignment copies identity, not the object |
| Pass by value | Parameter reassignment does not reassign the caller's variable |
| Definite assignment | Local variables need initialization on every read path |
| Numeric conversion | Widening can still lose floating-point precision |
| Integer division | Convert an operand before dividing if fractions are required |
| Overflow | Ordinary integer arithmetic can wrap; checked Math operations detect overflow |
| Overload resolution | Start with compile-time argument types and applicability phases |
| Boxing/unboxing | Wrapper identity is not general value equality; null unboxing fails |
| Short circuit | The right operand may not execute |
| String equality | equals for content; == for identity |
| String length | UTF-16 code units, not necessarily visible characters |
| StringBuilder | Suitable for deliberate incremental text construction |
| Arrays | Fixed length; enhanced-for reassignment does not replace a slot |
| Class loading | Loading, linking and initialization have different responsibilities |
| Initialization | Active use and constant access can have different effects |
| Reflection | Access and module boundaries still matter |
| Parsing | Validate format, range, locale and input limits |
| Scanner | Token reads and line reads consume different boundaries |

## Check yourself

### 1. Lost fraction

Why does converting the result of integer division to double not restore a fractional part?

**Answer:** The integral operation has already computed its truncated result. Convert an operand before the division so the operation itself uses floating-point arithmetic.

### 2. Array mutation versus reassignment

A method sets values[0] to 9 and then assigns values to a new array. Which change can the caller observe through its original reference?

**Answer:** The element mutation affects the shared original array. Reassigning the local parameter only changes that parameter's copied reference.

### 3. Advanced: overloaded primitive and wrapper

Why does example C2 choose long rather than Integer?

**Answer:** A widening primitive conversion is applicable during the strict-invocation phase, before the phase allowing boxing is needed. The literal's compile-time type is int.

### 4. Advanced: nullable numeric field

A database mapping returns an Integer that is null. Why can adding one throw an exception although addition itself has no explicit null check?

**Answer:** Unboxing is required before arithmetic. Dereferencing the absent wrapper fails before the numeric operation can occur.

### 5. Advanced: visible character count

A string contains one supplementary Unicode code point. Must length() return one?

**Answer:** No. Such a code point uses a surrogate pair and therefore two UTF-16 code units. User-perceived character boundaries can be more complex still.

### 6. Constant versus active initialization

Can a caller read a compile-time constant without producing the same initialization trace as example C3?

**Answer:** Yes. Constant values may be incorporated into the caller, so reading them need not initialize the declaring class in the same way as reading its nonconstant static field.

## Sources

Reviewed 2026-09-25. Baseline: Java SE 17. Programs are original and checked with the declared --release target.

- [JLS 17 types and variables](https://docs.oracle.com/javase/specs/jls/se17/html/jls-4.html).
- [JLS 17 conversions and contexts](https://docs.oracle.com/javase/specs/jls/se17/html/jls-5.html).
- [JLS 17 execution and initialization](https://docs.oracle.com/javase/specs/jls/se17/html/jls-12.html).
- [JLS 17 expressions](https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html).
- [Java 17 String API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/String.html).
- [Java 17 Integer API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Integer.html).
- [Java 17 Math API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Math.html).
- [Java 17 Scanner API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Scanner.html).
- [Java 17 AccessibleObject API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/reflect/AccessibleObject.html).
