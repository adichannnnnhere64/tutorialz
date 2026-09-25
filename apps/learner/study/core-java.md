## Understand

A Java program combines values, decisions and methods. Primitive variables hold values; reference variables identify objects or hold `null`. Assigning a reference copies that reference, so two variables can reach the same mutable object. Java passes every method argument by value, including object references.

Integer types are `byte` (8 bits), `short` (16), `int` (32) and `long` (64). `float` and `double` use binary floating point. `char` is a 16-bit UTF-16 code unit; one visible character can need two code units. `boolean` has `true` and `false`; Java does not promise a one-bit storage layout. Fields and array elements receive defaults; local variables must be definitely assigned before use.

Use `if` for conditions, `switch` for alternatives, and loops for repetition. A `for` loop runs initialization once, then condition, body and update. `break` exits a loop; `continue` starts the next iteration. In a `for` loop the update still runs after `continue`.

## Apply

This complete Java 17 program prints `2:2.5:10`:

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

Integer division truncates toward zero. Casting the result of `5 / 2` to `double` cannot restore the lost fraction; convert an operand before division. Numeric narrowing may lose information. Parsing, such as `Integer.parseInt("42")`, converts text and may throw `NumberFormatException`.

## Cheatsheet

| Need | Use / remember |
| --- | --- |
| Compare String contents | `a.equals(b)`; `Objects.equals(a,b)` handles nulls |
| Build repeated text | `StringBuilder.append(...)`, then `toString()` |
| Length | Array: `a.length`; String: `s.length()`; collection: `c.size()` |
| Boolean short circuit | `&&` and `\|\|`; `&` and `\|` also evaluate the right operand |
| String slices | `substring(start,end)` excludes `end` |
| Arrays | Zero-based, fixed length; enhanced-for does not replace stored elements |
| Scanner | `nextInt()` leaves the line separator for a following `nextLine()` |
| Math | `abs`, `min`, `max`, `sqrt`, `pow`; overflow still matters |

Strings are immutable. `==` compares reference identity. `static` members belong to the class, while instance members belong to each object. A method's parameter types determine overload selection; its return type alone cannot distinguish overloads.

## Check yourself

Why does `int x = 3; change(x);` leave `x` unchanged when `change(int value)` assigns `value = 9`?

**Answer:** The method receives a copy of the primitive value. With an object parameter it receives a copy of the reference: it can mutate the referenced object, but reassigning the parameter does not reassign the caller's variable.

## Sources

[Java language basics](https://dev.java/learn/language-basics/) · [Oracle: primitive types](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html) · [Princeton quick reference](https://introcs.cs.princeton.edu/java/11cheatsheet/)
