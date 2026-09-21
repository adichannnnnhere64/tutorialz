"""One beginner repair per concept; OOP scenarios are authored in oop_content.py."""
from __future__ import annotations

import json
from pathlib import Path

from oop_content import course as oop_course
from question_bank import assessment, choice, preserve_revisions, slug

BEGINNER = """
Program entry point|main is the conventional launcher entry method|public static void main(String[] args)|starting a class that has no suitable main method|add a suitable main method to the launched class
Source file extension|Java source files normally use the .java extension|Save a public Hello class in Hello.java|saving the source only as Hello.txt|save Java source with a .java extension
Public class filename|a public top-level class must match its source filename|public class Hello in Hello.java|putting public class Hello in Welcome.java|rename the file or the public class to match
Compilation|javac compiles source into class files|javac Hello.java|running javac on a nonexistent source path|supply the correct source file path to javac
Running a class|java launches a compiled class by its class name|java Hello|using java Hello.java when intending to run a compiled Hello class|launch the compiled class by name
Statements|a simple Java statement commonly ends with a semicolon|int count = 1;|writing int count = 1 without its semicolon|end the declaration statement with a semicolon
Blocks|braces group statements into a block|if (ready) { start(); }|leaving a required closing brace out of a block|close the block with a matching brace
Line comments|two slashes begin a comment to the end of the line|// explain the next step|expecting text after // on that line to execute|put executable code on an uncommented line
Block comments|slash-star and star-slash delimit a block comment|/* explanation */|forgetting to close a block comment|close the comment with */
Identifiers|a variable name cannot start with a digit|int item2 = 4;|declaring int 2item = 4;|choose an identifier that does not start with a digit
Case sensitivity|Java treats names with different letter case as distinct|count and Count are different names|using Count after declaring only count|use the exact declared capitalization
Variable declaration|a variable declaration gives a type and a name|int age;|using age before declaring it|declare age with a suitable type before use
Local initialization|a local variable must be assigned before its value is read|int age = 20; print(age);|reading a local age before assignment|assign the local variable before reading it
Integer type|int stores a signed 32-bit integer|int count = 12;|assigning a decimal fraction directly to int|choose a suitable floating-point type or convert explicitly
Long literals|an L suffix makes an integer literal long|long size = 3000000000L;|using an out-of-range unsuffixed int literal|add L to the long literal
Floating-point default|a decimal floating-point literal is double by default|double price = 1.5;|assigning 1.5 directly to float|use 1.5f or a double variable
Float literals|an f suffix marks a float literal|float rate = 1.5f;|assigning an unsuffixed decimal literal to float|add the f suffix to the float literal
Boolean values|boolean has true and false values|boolean ready = true;|assigning the string "true" to a boolean|use the boolean literal true
Character literals|a char literal uses single quotes|char grade = 'A';|using double quotes for a char literal|use single quotes for one character
String literals|a String literal uses double quotes|String name = "Ada";|using single quotes around multiple characters|use double quotes for a String
String concatenation|plus joins strings into a new String|"Hi " + name|expecting plus on Strings to perform numeric addition|use plus to concatenate textual values
Assignment|one equals sign assigns a value|count = 3;|using == when intending to assign a value|use = for assignment
Equality comparison|two equals signs compare primitive values|count == 3|using = when intending to compare primitive values|use == for the primitive comparison
Not equal comparison|!= tests whether values differ|count != 0|using =! as a not-equal operator|use != for inequality
Logical AND|&& requires both boolean operands to be true|ready && valid|using & when short-circuit evaluation is needed|use && for short-circuit boolean AND
Logical OR|the logical OR operator succeeds when either boolean operand is true|a condition is true when ready or retry is true|using a single pipe when short-circuit OR is needed|use the double-pipe operator for short-circuit boolean OR
Logical NOT|! reverses a boolean value|!ready|writing not ready as Java syntax|use ! before the boolean expression
Remainder|% returns the remainder of integer division|7 % 3 gives 1|using / to calculate a remainder|use the % operator
Integer division|division of two ints discards the fractional part|7 / 2 gives 3|expecting 7 / 2 to produce 3.5|convert an operand to a floating-point type first
Increment|++ increases a numeric variable by one|count++;|expecting count++ to add two|use ++ for one step or += 2 for two
Compound assignment|+= adds and assigns in one expression|count += 2;|writing count + 2; and expecting count to change|assign the result or use +=
If statement|if executes a branch when its condition is true|if (ready) { start(); }|using a non-boolean int directly as an if condition|write a boolean expression in the condition
Else branch|else runs when the paired if condition is false|if (ready) start(); else waitForReady();|expecting else to run after a true if branch|put the alternate action in else
Else-if chain|else if checks another condition after earlier conditions fail|if (score > 90) a(); else if (score > 80) b();|expecting every else-if branch to run|use separate if statements when all checks must run
For loop|for combines initialization, condition, and update|for (int i = 0; i < 3; i++) { work(); }|forgetting to update a loop counter that must advance|update the counter in the loop
While loop|while checks its condition before each iteration|while (ready) { work(); }|expecting a false while condition to run once|use do-while if one execution is required
Do-while loop|do-while checks its condition after the body|do { read(); } while (retry);|expecting do-while to skip a false initial condition|use while when the body should possibly be skipped
Break statement|break exits the nearest loop or switch|if (done) break;|expecting break to exit every enclosing loop|use explicit control flow for outer loops
Continue statement|continue skips to the next loop iteration|if (skip) continue;|using continue when the entire loop should stop|use break to exit the loop
Array declaration|an array variable names an array type|int[] scores;|treating int scores as an array declaration|declare the variable with []
Array creation|new creates an array with a fixed length|int[] scores = new int[3];|expecting an array to grow when indexed beyond its length|create an array of the needed size or use a list
Array indexing|array indexes start at zero|scores[0] accesses the first element|using scores[1] to access the first element|use index 0 for the first element
Array length|an array exposes its length through a field|scores.length|calling scores.length() on an array|read the length field without parentheses
Enhanced for loop|an enhanced for loop visits elements in sequence|for (int score : scores) { print(score); }|expecting the loop variable to be an array index|use an indexed loop when an index is needed
Method declaration|a method declares return type, name, and parameters|int twice(int n) { return n * 2; }|declaring a non-void method with no returned value|return a value of the declared type
Void method|void marks a method with no result value|void greet() { print("Hi"); }|trying to use a void method call as an int value|use a return type when a value is required
Method argument|an argument supplies a value to a parameter|twice(4)|calling twice() when twice requires an int|pass an int argument
Return statement|return ends a method invocation and can supply its result|return count;|expecting statements after an unconditional return to execute|place needed work before return
Scope|a local variable is visible only inside its declared scope|int x inside a method block|using a block-local x after the block closes|declare shared state in an enclosing scope when appropriate
Null reference|null denotes no object reference|String name = null;|calling name.length() while name is null|assign a non-null String before invoking a method
String length|String.length() returns the number of UTF-16 code units|"cat".length() gives 3|reading a String length field as text.length|call the length() method on a String
String equality|String.equals compares String contents|"cat".equals(name)|using == to compare String contents|use equals for content equality
String immutability|a String operation does not modify the existing String|name = name.trim();|calling name.trim() without using its returned String|store or use the returned String
Parsing an integer|Integer.parseInt converts decimal text to int|Integer.parseInt("42")|assigning "42" directly to an int|parse the text as an integer
Try-catch|catch handles a matching thrown exception|try { parse(); } catch (NumberFormatException e) { recover(); }|expecting catch to run when no exception is thrown|put recovery in the matching catch path
Finally block|finally runs after try or catch during normal completion or exception propagation|finally { close(); }|putting normal result logic only in finally|use finally for cleanup
Package declaration|package gives a source file its package name|package example.app;|expecting a class in a named package to be in the unnamed package|use the declared package when referencing the class
Import declaration|import lets source use a type's simple name|import java.util.List;|expecting an import to instantiate a List|create or obtain an object separately from importing its type
Static import|static import allows unqualified access to a static member|import static java.lang.Math.PI;|expecting a static import to create an object|use static import only for static members
Type inference with var|var infers a local variable's static type from its initializer|var name = "Ada";|declaring var name; without an initializer|initialize a var local variable in its declaration
""".strip().splitlines()

# Plausible misconceptions about the same rule, rather than unrelated topics.
# The default floating-point type and f suffix share one repair assessment.
DISTRACTORS = """
Program entry point|rename any method to start|make the class abstract so the launcher supplies main|add a constructor named main
Source file extension|rename the source to Hello.class without compiling it|save only Hello.jar as plain source text|change the class name to Hello.txt
Public class filename|make the constructor name match Welcome while leaving the class Hello|add an import for Welcome|add a second public class named Welcome to the same file
Compilation|use java on the same missing path|rename the missing output class without supplying source|remove the .java extension from the missing path
Running a class|launch Hello.class as the class name|supply javac as the application class|rename the compiled class file to Hello.java
Statements|end the declaration with a colon|put a comma after the declaration|use an empty comment in place of the terminator
Blocks|add another opening brace at the end|replace the missing brace with a semicolon|indent the last statement to close the block
Line comments|add a semicolon after the commented text to execute it|indent the text after // to make it executable|use uppercase letters after // to end the comment
Block comments|close the comment with //|close the comment with a brace|insert a newline to end every block comment
Identifiers|put quotes around 2item to make it an identifier|import a variable named 2item|declare 2item final to allow the leading digit
Case sensitivity|add final to make names case-insensitive|capitalize all uses without changing the declaration|add an import to alias Count to count
Variable declaration|use age first so Java infers its type from the later call|add parentheses around the undeclared name|write age as a comment before using it
Local initialization|rely on every local int starting at zero|mark the unassigned local final and read it|add an import to initialize the local automatically
Integer type|append f while leaving the variable int|put the fraction in quotes and assign it to int|declare the int final to permit fractional values
Long literals|append f to preserve the exact integer as a long literal|cast the already out-of-range unsuffixed literal to long|put the digits in quotes and assign the String directly to long
Floating-point default|leave 1.5 unchanged because every decimal literal is float|append L to the decimal literal|make the float variable final without changing the literal
Boolean values|cast the String directly to boolean|use the integer 1 as a boolean literal|remove quotes and use yes as a built-in boolean literal
Character literals|keep double quotes and make the char final|add a second character inside single quotes|use a String cast as an automatic char conversion
String literals|keep multiple characters in single quotes|use backticks as Java String delimiters|omit all delimiters so the words become a literal
String concatenation|cast the combined String directly to int|use == to add two numeric Strings|use multiplication to concatenate instead of plus
Assignment|use === to assign the new value|reverse == to =! for assignment|add parentheses around the equality comparison to make it assign
Equality comparison|use = and rely on automatic boolean conversion|use === for primitive equality in Java|use != when testing whether both values are the same
Not equal comparison|use <> as the Java inequality operator|put spaces inside =! to make it valid|replace the comparison with assignment
Logical AND|keep & because it skips the right operand when the left is false|use logical OR to require both operands to be true|use ! on the right operand to create short-circuit AND
Logical OR|use && so either operand can make the result true|keep the single pipe because it always skips an unnecessary right operand|add ! to both operands instead of using OR
Logical NOT|write NOT as an uppercase keyword|use ~ on the boolean expression|compare the boolean to the integer zero
Remainder|use / and keep the quotient|use // as the remainder operator|use %% as a separate Java operator
Integer division|cast the integer result to double only after dividing|store the int division result in a double and expect the fraction back|append a decimal point to the variable name
Increment|apply ++ twice and expect only one increment|replace ++ with -- to increase the value|make the variable final before incrementing it
Compound assignment|leave count + 2 as a standalone Java expression statement|use count == count + 2 to store the sum|make count final so addition updates it automatically
If statement|use a nonzero int because Java treats it as true|cast the int directly to boolean|surround the int with extra parentheses to make it boolean
Else branch|put the alternate action inside the true branch|add another else to force both branches to run|use else without a matching if to run after every condition
Else-if chain|raise the first matching threshold so every later else-if executes|add braces around the same else-if chain to run every branch|replace all conditions with assignment expressions
For loop|make the counter final so it advances automatically|add a semicolon immediately after the loop header to increment it|move the counter declaration outside the loop without ever updating it
While loop|add braces to guarantee one iteration even when false|initialize the condition to false to force the first iteration|place a semicolon after while so the body runs exactly once as part of the loop
Do-while loop|add braces to skip the first body execution|put false in the trailing condition to prevent all body executions|use continue before the condition to undo the first iteration
Break statement|add a second break after the first unconditional break|use continue to exit all enclosing loops|indent break under the outer loop to change its target
Continue statement|add another continue immediately afterward|use return to exit only the current iteration while keeping the method running|use a semicolon after continue to terminate the whole loop
Array declaration|declare int scores and rely on later indexing to turn it into an array|use angle brackets int<scores>|declare array int scores without square brackets
Array creation|write to scores[scores.length] to append automatically|increase scores.length with ++|cast scores to a longer array without allocating one
Array indexing|use index 1 because Java arrays are one-based|use index -1 for the first element|use the length as the first valid index
Array length|keep length() because every array field is a method|use size() because all arrays implement List|subtract one from the last index to get every array length
Enhanced for loop|use the element value as an index for every array|increment the enhanced-for variable to make the array longer|assign to the loop variable to replace every primitive array element
Method declaration|change the method name to the return type|add a semicolon after the body to return automatically|rely on an implicit zero result from every non-void method
Void method|cast the void result to int|assign the void call to an Integer instead|make the method public so its void call produces a value
Method argument|call twice() because missing int arguments default to zero|put the int value after the call's closing parenthesis|declare the result variable final to supply the argument
Return statement|add another return after the unconditional return|put needed work immediately after return in the same block|make the method static so execution continues after return
Scope|indent the later use into the old scope without changing braces|mark the block-local variable final to extend its visibility|add an import for the local variable
Null reference|cast null to String so method calls succeed|call length first and check for null afterward|compare the null reference to an empty String using its instance equals method
String length|read text.length as though String were an array|read text.size without calling a method|use text.capacity() as a String method
String equality|use == because it always compares character sequences|use = to compare String values|call hashCode and assume equal hashes guarantee equal text
String immutability|mark name final so trim modifies the original String|call trim repeatedly until the original String mutates|assign the result of length() back to the same String variable
Parsing an integer|cast the String object directly to int|remove the quotes at runtime by subtracting an empty String|assign the String to Integer using automatic unboxing
Try-catch|expect catch to execute once on every successful call|put an unconditional return before try so catch runs|use finally instead of catch to identify only NumberFormatException
Finally block|return every success result from finally even when it suppresses a failure|put cleanup after a return in the same try block|assume a matching catch always replaces the need for cleanup
Package declaration|ignore the declaration because folder names always override it|import the package as though it were an object instance|remove dots from the qualified class name without moving the type
Import declaration|call a constructor by writing an import inside a method|expect the import to allocate one object per use|use import instead of new to choose a list implementation
Static import|use static import to construct the declaring class|import an instance field statically without an object|write a constructor call in the static import declaration
Type inference with var|assign null alone and expect a useful inferred class type|declare var as a field without a type or initializer|use var for a method parameter in an ordinary named method
""".strip().splitlines()


PROMPTS = """
Program entry point|`java Hello` reports that no main method was found. Hello is intended to be a Java 17 console application. What needs to be added?
Source file extension|A Java source file is saved as Hello.txt. Which change makes its filename suitable for the usual javac source-file workflow?
Public class filename|Welcome.java declares `public class Hello`. What fixes the public-class filename mismatch?
Compilation|`javac src/Hello.java` reports that the source file does not exist. The file is actually in app/Hello.java. What should the command use?
Running a class|Hello.class has already been compiled in the current directory, and no Hello.java source is available. How should it be launched from that directory?
Statements|The declaration `int count = 1` appears inside a method without a terminator. Which correction completes this declaration statement?
Blocks|An if block opens with `{` but never closes before the surrounding method ends. What fixes the unmatched block?
Line comments|In `// count++;`, the increment never executes. What must change to make it executable code?
Block comments|A `/*` comment accidentally includes the rest of the source file. How should the intended comment be closed?
Identifiers|Why must `int 2item = 4;` be changed, and which naming rule should the replacement follow?
Case sensitivity|A method declares count but later reads Count. How should the unresolved name be corrected?
Variable declaration|A method tries to assign to age, but no local, parameter, or field named age exists. What must be added before use?
Local initialization|`int age; System.out.print(age);` appears inside a method. What is required before the print statement?
Integer type|`int price = 12.75;` does not compile. Which type or conversion decision is required for the fractional value?
Long literals|`long size = 3000000000;` fails because the unsuffixed literal is out of range. How should the exact long literal be written?
Floating-point default|`float rate = 1.5;` fails with a possible loss of precision. Which correction fits Java's literal typing rules?
Boolean values|`boolean ready = "true";` does not compile. Which value belongs on the right side for a true boolean?
Character literals|`char grade = "A";` does not compile. How should the single character literal be delimited?
String literals|`String name = 'Ada';` uses invalid literal syntax. What should delimit the text?
String concatenation|A greeting and a name are both Strings. Which use of plus correctly combines their text?
Assignment|`count == 3;` was intended to store 3 in count. Which operator should be used for that update?
Equality comparison|`if (count = 3)` does not compare count with 3. Which change produces the intended primitive equality test?
Not equal comparison|`count =! 0` was intended to test whether count differs from zero. Which operator is required?
Logical AND|A condition must be true only when ready and valid are true, and valid must not be evaluated when ready is false. Which operator fits?
Logical OR|A fallback condition must be evaluated only when the first condition is false. Which boolean OR operator provides that behavior?
Logical NOT|ready is a boolean. What should replace the invalid expression `not ready` to reverse its value?
Remainder|The expression `7 / 3` produces a quotient, but the program needs the remainder. Which operator should replace division?
Integer division|`double average = 7 / 2;` stores 3.0. How can the division itself produce 3.5?
Increment|count starts at 4. The statement `count++;` leaves it at 5, but the intended result was 6. Which correction matches the required step?
Compound assignment|`count + 2;` neither forms a valid standalone Java expression statement nor stores the sum. Which change updates count?
If statement|`if (count)` uses an int as a condition. What must replace count in the condition?
Else branch|An alternate action should run only when ready is false in an if/else pair. Where should that action go?
Else-if chain|Several independent conditions may be true, and every matching action must run. An else-if chain runs only the first match. What structure is needed?
For loop|A for loop's counter never changes, so its true condition never becomes false. Where should the required counter update be supplied?
While loop|A loop body must run once even when its initial continuation condition is false. Which loop form meets that requirement?
Do-while loop|A do-while body runs once with an initially false condition, but zero iterations are required in that case. Which loop form should be used?
Break statement|An unlabeled break inside nested loops exits only the inner loop. What is needed to also leave the outer loop?
Continue statement|Finding a target should end the loop, but continue merely advances to another iteration. Which statement matches the intended behavior?
Array declaration|scores must refer to an int array, but `int scores;` declares a scalar. What must be included in its declaration?
Array creation|An int array is full, and writing at its length index fails. What storage change is needed to support more elements?
Array indexing|The program reads `scores[1]` but needs the first element of a nonempty Java array. Which index should it use?
Array length|`scores.length()` fails when scores is an int array. How should its element count be accessed?
Enhanced for loop|In `for (int score : scores)`, score is an element value. The algorithm also needs each position. Which loop approach should be used?
Method declaration|`int twice(int n) { int result = n * 2; }` computes a value but has no return. What must the method supply?
Void method|A caller tries `int result = greet();`, but greet returns void. What must the API provide if this call should produce an int result?
Method argument|`int twice(int n)` requires a parameter, but the caller writes twice(). What must the invocation supply?
Return statement|A required update appears immediately after an unconditional return in the same block. Where should that update be moved?
Scope|A variable declared inside an if block is needed by later code outside that block. Where should its declaration be placed if both uses must share it?
Null reference|`String name = null; name.length();` fails at runtime. What is needed before this method invocation can succeed?
String length|`text.length` fails when text is a String. How should its length be read?
String equality|Two separately created Strings contain the same text, but == reports false. Which comparison expresses equality of their contents?
String immutability|Calling `name.trim();` leaves name referring to the original String. How should the trimmed result be used?
Parsing an integer|The program receives the text "42" and needs its numeric int value. Which conversion should be performed?
Try-catch|Parsing invalid decimal input may throw NumberFormatException. Where should recovery for that failure be placed?
Finally block|Cleanup is needed whether a try block completes normally or throws. Which purpose should the finally block serve?
Package declaration|A class declares `package example.app;`, but other code treats it as being in the unnamed package. What must references account for?
Import declaration|`import java.util.List;` makes the type name available but no list object exists. What additional action is needed to use an instance?
Static import|A static import is expected to create a Math object. What does the import actually allow instead?
Type inference with var|`var name;` has no initializer. What must be supplied so Java can infer the local variable's type?
""".strip().splitlines()


def courses() -> list[dict]:
    distractors = {row[0]: row[1:] for line in DISTRACTORS if (row := line.split("|"))}
    prompts = dict(line.split("|", 1) for line in PROMPTS)
    tests = []
    for group in range(6):
        questions = []
        for index in range(group * 10, group * 10 + 10):
            topic, rule, example, mistake, repair = BEGINNER[index].split("|")
            if topic == "Float literals":
                continue  # The default-type repair already tests the f suffix.
            concepts = [slug(topic)]
            if topic == "Floating-point default":
                concepts.append("float-literals")
            q = choice(
                f"java-beginner-java-{index + 1:03d}-11",
                prompts[topic],
                repair, distractors[topic],
                f"{topic}: {rule}. {repair[0].upper() + repair[1:]}. Example: {example}.",
                topic, "https://dev.java/learn/language-basics/",
                assessment(f"java-{slug(topic)}-repair", "debug", *concepts), "easy",
            )
            questions.append(q)
        tests.append({"id": f"beginner-java-practice-{group + 1}",
                      "title": ["Getting a program running", "Names and values", "Operators",
                                "Control flow", "Arrays and methods", "Strings and program structure"][group],
                      "description": "Correct common Java mistakes using choices about the same concept.",
                      "difficulty": "easy", "questions": questions})
    imported = json.loads((Path(__file__).resolve().parents[1] / "content/enterprise/imports/java-quiz-selected.json").read_text())
    tests.append({"id": "beginner-java-imported-practice", "title": "Types, operators, and library methods",
                  "description": "Five reviewed questions imported from Tahir Naseer's MIT-licensed Java quiz.",
                  "difficulty": "easy", "questions": imported})
    total = sum(len(test["questions"]) for test in tests)
    return [{"schema_version": 1, "id": "beginner-java", "title": "Java fundamentals — Beginner",
             "description": f"{total} focused Java 17 questions: practical repairs and five attributed imports.",
             "subject": "Java fundamentals", "difficulty": "easy", "lessons": [], "tests": tests}, oop_course()]


def generate(out: Path, write_json) -> list[dict]:
    entries = []
    for course in courses():
        path = out / f"{course['id']}.json"
        preserve_revisions(course, json.loads(path.read_text()) if path.exists() else None)
        digest = write_json(path, course)
        entries.append({key: course[key] for key in ("id", "title", "description", "subject", "difficulty")} |
                       {"path": path.name, "sha256": digest})
    return entries
