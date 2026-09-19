"""Generate original Java language and OOP practice from curated concept rows.

Rows describe one rule, one concrete use, one common mistake, and a repair. The
variants test recognition and application of that rule; they are not independent
facts. Sources are official Oracle Java language tutorials.
"""
from __future__ import annotations

import json
from pathlib import Path

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

OOP = """
Class blueprint|a class declares the state and behavior of its instances|class Account { private int balance; }|using one mutable global value for every customer's balance|give each Account instance its own balance field
Object instance|an object is an instance created from a class|Account a = new Account();|treating a class declaration as an already-created account|construct an Account instance before using instance methods
Reference identity|two references can point at the same object|Account b = a;|expecting b = a to copy every field into a new Account|create a separate object when independent identity is required
Instance state|each object has its own instance field values|a.balance differs from b.balance for separate objects|using static for per-customer balance|store per-customer data in instance fields
Static state|a static field is associated with a class|static int instanceCount;|using a static balance for independent accounts|reserve static state for class-wide data
Encapsulation|a class can hide state behind methods|private balance with deposit()|allowing callers to write any balance directly|make balance private and expose checked operations
Data validation|mutator methods can enforce object invariants|deposit rejects a negative amount|accepting a negative deposit without a rule|validate the amount before changing state
Private access|private members are accessible within their declaring class|private int balance;|accessing account.balance from unrelated code|call an accessible method instead
Public access|public members can be accessed wherever the type is accessible|public int balance()|expecting public to limit calls to one package|choose narrower access for internal APIs
Protected access|protected supports package and subclass access under Java rules|protected void recalculate()|assuming protected means only subclasses can access it|review package access as well as subclass access
Package-private access|omitting an access modifier gives package access|void recalculate()|expecting an unmodified method to be public|declare public if external packages must call it
Constructor initialization|a constructor initializes a newly created instance|new Account(100)|assuming constructors are inherited by subclasses|declare the needed subclass constructor explicitly
No-arg constructor|a compiler adds a default no-arg constructor only when none is declared|new Account() when no constructor is declared|adding Account(int) then assuming new Account() still works|declare an explicit no-arg constructor if needed
Constructor chaining|this(...) invokes another constructor of the same class|Account() { this(0); }|repeating initialization inconsistently across constructors|delegate shared setup through a constructor
Superclass construction|super(...) invokes a superclass constructor|Child() { super(1); }|assuming a superclass with only a parameterized constructor needs no call|invoke an accessible superclass constructor
This reference|this denotes the current object|this.balance = balance;|assigning a shadowing parameter to itself|use this.field to distinguish the instance field
Inheritance|a subclass can reuse and specialize a superclass|class Savings extends Account|using inheritance for two unrelated classes that merely share a helper|extract a shared component or interface instead
Single class inheritance|a Java class has at most one direct superclass|class Savings extends Account|trying to extend two classes at once|extend one class and use interfaces for additional contracts
Subclass substitutability|a subclass should honor the base type's observable contract|Account a = new Savings();|making a subclass reject valid base-class operations unexpectedly|preserve the base contract or use composition
Overriding|an instance method can replace inherited behavior with a compatible signature|@Override public String toString()|changing only the return type to an incompatible type|match the inherited method signature and compatible return type
Override annotation|@Override asks the compiler to verify an override|@Override void draw()|misspelling a method name while expecting an override|add @Override and fix the signature
Overloading|methods can share a name with different parameter lists|print(int n) and print(String s)|declaring two methods that differ only by return type|change the parameter list for a valid overload
Dynamic dispatch|an overridden instance method is selected from the runtime object type|Shape s = new Circle(); s.draw();|expecting s.draw() to always call Shape.draw()|account for the Circle override at runtime
Field hiding|fields are selected from the reference type rather than dynamically overridden|a hidden field accessed through a Base reference|expecting fields to dispatch like overridden methods|expose behavior through methods instead of hidden fields
Static method hiding|a static method is hidden rather than overridden|Child.utility() hides Base.utility()|expecting static methods to use runtime dispatch|call static methods through their declaring type
Final method|a final method cannot be overridden|final void verify()|trying to override a final verify method|remove the override or redesign the extension point
Final class|a final class cannot be subclassed|final class Token|trying to extend a final class|use the class through composition
Abstract class|an abstract class cannot be directly instantiated|abstract class Shape|calling new Shape() when Shape is abstract|instantiate a concrete subclass
Abstract method|a concrete subclass must implement inherited abstract methods|abstract double area();|leaving area() unimplemented in a concrete subclass|implement area() or keep the subclass abstract
Interface contract|an interface declares a type contract implemented by classes|class Circle implements Drawable|treating an interface as an instantiated concrete class|instantiate a class implementing the interface
Multiple interfaces|one class may implement more than one interface|class Job implements Runnable, AutoCloseable|trying to extend two classes for two roles|implement multiple interfaces when appropriate
Interface default method|a default method supplies an interface implementation|default void reset() { }|assuming every default method must be implemented again|inherit it unless customization is needed
Interface static method|an interface static method is called on the interface type|Comparator.naturalOrder()|expecting an interface static method to be inherited as an instance method|call it through the interface name
Composition|an object can delegate to contained collaborators|Car has an Engine field|subclassing Engine just to let Car use one|store an Engine collaborator in Car
Dependency injection|a collaborator can be passed to a constructor|Service(Repository repository)|constructing a fixed repository inside every service constructor|accept the repository as a dependency
Polymorphic collection|a base type collection can hold different implementations|List<Shape> shapes with Circle and Square|writing one loop per concrete shape solely to call area()|iterate the base type and invoke the common method
Upcasting|a subtype reference can be assigned to a supertype variable|Shape shape = new Circle();|expecting upcasting to erase the object's Circle behavior|use the base reference while runtime overrides remain available
Downcasting|a cast to a subtype needs a compatible runtime object|if (s instanceof Circle) { Circle c = (Circle) s; }|casting every Shape to Circle without checking|check the runtime type before a necessary cast
Instanceof test|instanceof checks whether an object has a compatible runtime type|shape instanceof Circle|expecting a null reference to match Circle|handle null separately when needed
Object equality|equals can define logical equality of objects|a.equals(b) for equal value objects|using == when logical value equality is intended|implement and call equals consistently
Hash code contract|equal objects must have equal hash codes|equal keys produce the same hashCode()|overriding equals without a consistent hashCode|override hashCode consistently with equals
ToString representation|toString supplies a textual representation of an object|account.toString()|printing a sensitive object with a secret-bearing toString|design a useful representation without secrets
Immutable object|an immutable object's observable state does not change after construction|final fields with no mutators|returning a mutable internal list directly|defensively copy mutable state at boundaries
Defensive copying|copies prevent callers from mutating internal objects|List.copyOf(items)|storing a caller-owned mutable list without protection|make a defensive copy before storing it
Interface segregation|small interfaces avoid forcing clients to depend on unrelated operations|Readable and Writable contracts|forcing a read-only class to implement write()|split broad contracts into focused interfaces
Open-closed design|new implementations can extend behavior through a stable contract|add a new PaymentMethod implementation|editing a long type switch for every new payment type|dispatch through a common interface
Liskov contract|subtypes should preserve valid expectations of the base type|a derived account honors the account contract|a subtype strengthens preconditions unexpectedly|keep subtype behavior compatible with base callers
Single responsibility|a class has one cohesive reason to change|InvoiceCalculator computes totals|one class computes totals, sends mail, and writes SQL|separate unrelated responsibilities into collaborators
Dependency inversion|high-level code can depend on abstractions|Checkout depends on PaymentGateway|Checkout constructs a specific StripeGateway internally|depend on a PaymentGateway interface and inject it
Association|one object may know and use another object|Order stores a Customer reference|calling every object relationship inheritance|model a uses-a relationship with a field
Aggregation|a container may reference parts that live independently|Team references existing Player objects|deleting Player solely because Team is removed|model independent part lifetimes
Composition ownership|a whole may manage a part's lifecycle|Order owns its LineItems|sharing a mutable owned LineItem across unrelated Orders|keep owned parts within their aggregate boundary
Nested class|a class can be declared inside another class|class Outer { static class Helper {} }|putting every helper in the same top-level namespace|nest a helper when it belongs to the enclosing type
Inner class|a non-static inner instance refers to an enclosing instance|outer.new Inner()|creating a non-static Inner without an Outer instance|create it through an enclosing object
Anonymous class|an anonymous class creates an unnamed implementation|new Runnable() { public void run() {} }|expecting an anonymous class to have a reusable declared name|use a named class if reuse or documentation is needed
Lambda target|a lambda can implement a functional interface|Runnable r = () -> work();|assigning a lambda to an interface with two abstract methods|use a functional interface target
Method reference|a method reference can supply compatible functional behavior|items.forEach(System.out::println)|using a method reference with an incompatible target signature|match the functional interface method signature
Generics|a generic type carries compile-time element information|List<String> names|putting an Integer into a List<String>|add elements matching the declared type argument
Inheritance and generics|List<Child> is not a subtype of List<Parent>|List<? extends Parent> view = children|assigning List<Child> directly to List<Parent>|use an appropriate wildcard view
Covariant return|an override may return a subtype of the original return type|Child copy() overrides Base copy()|returning an unrelated type from an override|choose the same return type or a valid subtype
""".strip().splitlines()

SOURCES = {
    "beginner-java": "https://dev.java/learn/language-basics/",
    "oop-medium": "https://dev.java/learn/classes-objects/",
}

LEADS = [
    "A learner is practicing Java fundamentals.",
    "A team discusses a small console exercise.",
    "A developer reviews a Java class.",
    "A student traces a Java program.",
    "A mentor checks a practice project.",
]


def parse(rows: list[str]) -> list[list[str]]:
    parsed = [line.split("|") for line in rows]
    assert len(parsed) == 60, len(parsed)
    assert all(len(row) == 5 and all(row) for row in parsed)
    assert len({row[0] for row in parsed}) == len(parsed)
    return parsed


def generate(out: Path, write_json) -> list[dict]:
    entries = []
    for course_id, raw, difficulty, count in [
        ("beginner-java", BEGINNER, "easy", 20),
        ("oop-medium", OOP, "medium", 10),
    ]:
        rows = parse(raw)
        path = out / f"{course_id}.json"
        previous = {}
        if path.exists():
            old = json.loads(path.read_text())
            previous = {q["id"]: q for test in old["tests"] for q in test["questions"]}
        tests = []
        for group in range(6):
            questions = []
            for index in range(group * 10, group * 10 + 10):
                topic, rule, example, mistake, repair = rows[index]
                for variant in range(count):
                    family, frame = divmod(variant, 5)
                    lead = LEADS[frame]
                    if family == 0:
                        prompt = f"{lead} Which statement best describes {topic} in Java?"
                        answer_field, answer = 1, rule
                    elif family == 1:
                        prompt = f"{lead} Which example correctly illustrates {topic}?"
                        answer_field, answer = 2, example
                    elif family == 2:
                        prompt = f"{lead} A programmer makes this mistake: {mistake}. What is the best correction?"
                        answer_field, answer = 4, repair
                    else:
                        prompt = f"{lead} Which topic explains this rule: {rule}?"
                        answer_field, answer = 0, topic
                    distractors = []
                    for step in range(1, 61):
                        candidate = rows[(index + 7 + variant * 3 + step * 11) % 60][answer_field]
                        if candidate != answer and candidate not in distractors:
                            distractors.append(candidate)
                        if len(distractors) == 3:
                            break
                    assert len(distractors) == 3
                    answers = [answer] + distractors
                    shift = (index + variant) % 4
                    options = answers[shift:] + answers[:shift]
                    question = {
                        "id": f"java-{course_id}-{index + 1:03d}-{variant + 1:02d}",
                        "revision": 1,
                        "prompt": prompt,
                        "difficulty": difficulty,
                        "explanation": f"{topic}: {rule}. Example: {example}. If {mistake}, {repair}.",
                        "type": "choice",
                        "options": options,
                        "correct": [(4 - shift) % 4],
                        "multiple": False,
                        "source_url": SOURCES[course_id],
                        "topic": topic,
                    }
                    old = previous.get(question["id"])
                    if old and {k: v for k, v in old.items() if k != "revision"} != {k: v for k, v in question.items() if k != "revision"}:
                        question["revision"] = old["revision"] + 1
                    elif old:
                        question["revision"] = old["revision"]
                    questions.append(question)
            tests.append({"id": f"{course_id}-practice-{group + 1}",
                          "title": f"{('Java basics' if difficulty == 'easy' else 'OOP')}: set {group + 1}",
                          "description": f"Practice ten concepts with {count} question variations each.",
                          "difficulty": difficulty, "questions": questions})
        total = len(rows) * count
        course = {"schema_version": 1, "id": course_id,
                  "title": "Java fundamentals — Beginner" if difficulty == "easy" else "Object-oriented Java — Medium",
                  "description": f"{total} original Java practice questions across {len(rows)} curated concepts.",
                  "subject": "Java fundamentals" if difficulty == "easy" else "Java OOP",
                  "difficulty": difficulty, "lessons": [], "tests": tests}
        digest = write_json(path, course)
        entries.append({key: course[key] for key in ("id", "title", "description", "subject", "difficulty")} |
                       {"path": path.name, "sha256": digest})
    return entries
