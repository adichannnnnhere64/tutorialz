"""Reviewed OOP assessments: each entry tests a different observable outcome.

Java examples target Java 17 without preview features. JAVA_CHECKS compiles the
same snippets displayed in prompts; it is authoring data, not learner payload.
"""
from copy import deepcopy
from question_bank import assessment, choice, slug

JLS = "https://docs.oracle.com/javase/specs/jls/se17/html/"
API = "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/"
JAVA_CHECKS = []
GROUPS = []


def group(title):
    GROUPS.append((title, []))


def ask(objective, topics, kind, prompt, answer, wrong, explanation, source):
    concepts = [slug(t) for t in topics]
    q = choice(f"java-oop-{objective}", prompt, answer, wrong, explanation,
               topics[0], source, assessment(f"java-{objective}", kind, *concepts))
    GROUPS[-1][1].append(q)
    return q


def code(objective, topics, declarations, body, answer, wrong, explanation, section):
    source = f"import java.util.*;\n{declarations}\npublic class Main {{\npublic static void main(String[] args) {{\n{body}\n}}\n}}\n"
    prompt = ("What is printed? Assume `java.util.*` is imported and the statements after the comment run inside `main`.\n\n"
              f"```java\n{declarations}\n// Inside main:\n{body}\n```")
    q = ask(objective, topics, "trace", prompt, f"`{answer}`",
            [f"`{w}`" for w in wrong], explanation, JLS + section)
    JAVA_CHECKS.append({"id": q["id"], "source": source, "stdout": answer})


group("Objects, state, and access")
code("independent-instance-fields", ["Class blueprint", "Object instance", "Instance state"],
     "class Account { int balance = 10; }",
     "Account a = new Account();\nAccount b = new Account();\na.balance += 5;\nSystem.out.print(a.balance + \":\" + b.balance);",
     "15:10", ["15:15", "10:10", "10:15"],
     "Each new Account has its own balance field. Updating a changes only that instance; b retains 10.",
     "jls-8.html#jls-8.3.1.1")
code("alias-mutation", ["Reference identity"],
     "class Box { int value = 1; }",
     "Box a = new Box();\nBox b = a;\nb.value = 7;\nSystem.out.print((a == b) + \":\" + a.value);",
     "true:7", ["false:1", "true:1", "false:7"],
     "Assignment copies the reference. Both variables designate the same Box, so a sees the mutation through b.",
     "jls-4.html#jls-4.3.1")
code("class-counter-and-instance-state", ["Static state"],
     "class Ticket {\n  static int count;\n  int number;\n  Ticket() { number = ++count; }\n}",
     "Ticket a = new Ticket();\nTicket b = new Ticket();\nSystem.out.print(a.number + \":\" + b.number + \":\" + Ticket.count);",
     "1:2:2", ["1:1:1", "2:2:2", "1:2:1"],
     "count is shared by both constructions. Each number stores the count at the time that particular Ticket is created.",
     "jls-8.html#jls-8.3.1.1")
code("reference-parameter-reassignment", ["Reference identity", "Method argument"],
     "class Box { int value = 1; }\nclass Update {\n  static void change(Box b) {\n    b.value = 2;\n    b = new Box();\n    b.value = 3;\n  }\n}",
     "Box original = new Box();\nUpdate.change(original);\nSystem.out.print(original.value);",
     "2", ["1", "3", "0"],
     "Java passes the reference value by value. The first mutation reaches the original Box, but reassigning b only changes the local parameter.",
     "jls-15.html#jls-15.12.4.5")
ask("guard-balance-invariant", ["Encapsulation", "Data validation"], "design",
    "An Account must always have a nonnegative balance. Withdrawals must reject nonpositive amounts and amounts above the balance. Which API protects that rule for every caller?",
    "Keep balance private; validate the amount and available balance inside withdraw before subtracting.",
    ["Expose a public balance field and validate only in the screen that edits it.",
     "Make balance protected and ask subclasses to avoid invalid assignments.",
     "Provide a public setBalance method that accepts any int."],
    "The object must enforce its invariant at each mutation boundary. Private storage plus a checked operation prevents callers from bypassing withdrawal rules.",
    JLS + "jls-6.html#jls-6.6")
ask("resolve-field-shadowing", ["This reference"], "debug",
    "A constructor is `Account(int balance) { balance = balance; }`. Its instance field remains zero. Which replacement stores the argument in the field?",
    "`this.balance = balance;`",
    ["`balance = this.balance;`", "`balance = Account.balance;`", "`this.balance = this.balance;`"],
    "The parameter shadows the field. this.balance selects the current object's field on the assignment's left side.",
    JLS + "jls-6.html#jls-6.4.1")
code("private-access-through-peer", ["Private access"],
     "class Box {\n  private int value;\n  Box(int value) { this.value = value; }\n  int read(Box other) { return other.value; }\n}",
     "System.out.print(new Box(1).read(new Box(9)));",
     "9", ["1", "0", "Compilation fails because other.value is private"],
     "Private access is governed by the enclosing class, not by which instance owns the field. Code inside Box can read a private field of another Box.",
     "jls-6.html#jls-6.6.1")
ask("public-member-hidden-type", ["Public access"], "debug",
    "In package library, top-level `class Helper` has a public constructor. Code in a different package tries `new library.Helper()`. Both packages are on the classpath. Why does compilation fail?",
    "Helper itself has package access, so the external code cannot name that type.",
    ["A public constructor can only be called from the same package.",
     "The external code must subclass Helper before constructing it.",
     "All top-level classes need a static modifier before external use."],
    "A public member does not make its declaring class public. The top-level Helper type must also be accessible to this client.",
    JLS + "jls-6.html#jls-6.6.1")
ask("protected-receiver-across-packages", ["Protected access"], "apply",
    "Public Base in package a declares `protected int value`. In package b, `class Child extends Base` has an instance method with parameters `Base base, Child child`. Which access is permitted inside that method?",
    "`child.value`, but not `base.value`",
    ["Both child.value and base.value", "base.value, but not child.value", "Neither access; protected is limited to package a"],
    "Outside Base's package, subclass access to this protected instance member requires a receiver whose type is Child or a subtype of Child. A Base-typed receiver does not satisfy that restriction.",
    JLS + "jls-6.html#jls-6.6.2.1")
ask("package-access-excludes-subpackages", ["Package-private access"], "apply",
    "Public class Report in package app has `void rebuild()`. A caller in package app.tools has a Report instance. Can it call rebuild()?",
    "No; app.tools is a different package, and rebuild has package access.",
    ["Yes; subpackages inherit access to their parent package.",
     "Yes; a public class makes all its methods public.",
     "No; an instance method must always be called from a subclass."],
    "Package names are not an access hierarchy. Omitting the method access modifier allows callers in app, not callers in app.tools.",
    JLS + "jls-6.html#jls-6.6.1")

group("Construction and initialization")
ask("restore-no-argument-construction", ["No-arg constructor"], "debug",
    "Account originally declared no constructors. After adding `Account(int opening)`, existing code using `new Account()` stops compiling. What preserves both forms of construction?",
    "Declare `Account() { this(0); }` in addition to Account(int).",
    ["Make Account(int) public; the compiler will supply Account().",
     "Give the opening parameter a default value in the parameter list.",
     "Add a void method named Account instead of a constructor."],
    "The compiler supplies a default constructor only when a class declares no constructors. An explicit no-argument constructor can delegate to the existing one.",
    JLS + "jls-8.html#jls-8.8.9")
ask("construct-subclass-explicitly", ["Constructor initialization"], "debug",
    "Base declares `Base(int id)`. Child extends Base and declares `Child() { super(0); }`. Why does `new Child(7)` fail?",
    "Constructors are not inherited; Child must declare its own constructor accepting int.",
    ["A subclass cannot have more than one constructor.",
     "A superclass constructor is inherited only if its parameter is final.",
     "Calling super(0) prevents all other Child constructors from being used."],
    "Constructor overloads belong to their declaring class. Add Child(int id) that explicitly calls super(id) to expose that construction path.",
    JLS + "jls-8.html#jls-8.8")
code("delegating-constructor-order", ["Constructor chaining"],
     "class Account {\n  Account() { this(4); System.out.print(\"B\"); }\n  Account(int n) { System.out.print(n); }\n}",
     "new Account();", "4B", ["B4", "4", "B"],
     "The this(4) invocation completes the int constructor before the no-argument constructor resumes and prints B.",
     "jls-8.html#jls-8.8.7.1")
ask("supply-required-super-argument", ["Superclass construction"], "debug",
    "For Java 17, Base has only `Base(int id)`. The declaration `class Child extends Base { Child() {} }` fails to compile. Which change fixes the missing superclass construction?",
    "Begin Child() with `super(1);`.",
    ["Insert `new Base(1);` in Child(); that initializes the superclass portion.",
     "Add `return;` to Child(); it skips superclass construction.",
     "Make Child() public; accessibility supplies the missing argument."],
    "Without an explicit constructor invocation, this constructor implicitly calls super(). Base has no such constructor. Creating a separate Base object does not initialize Child's superclass state.",
    JLS + "jls-8.html#jls-8.8.7")
code("superclass-before-subclass-initializers", ["Superclass construction", "Instance state"],
     "class Base { Base() { System.out.print(\"B\"); } }\nclass Child extends Base {\n  int n = init();\n  int init() { System.out.print(\"I\"); return 1; }\n  Child() { System.out.print(\"C\"); }\n}",
     "new Child();", "BIC", ["IBC", "BCI", "CIB"],
     "Superclass construction runs first. Child's instance field initializer then runs before the rest of the Child constructor body.",
     "jls-12.html#jls-12.5")
code("virtual-call-during-construction", ["Dynamic dispatch", "Constructor initialization"],
     "class Base {\n  Base() { System.out.print(value()); }\n  int value() { return 1; }\n}\nclass Child extends Base {\n  int n = 7;\n  int value() { return n; }\n}",
     "new Child();", "0", ["1", "7", "Compilation fails because constructors cannot call methods"],
     "Dispatch reaches Child.value even during Base construction. Child's field initializer has not run yet, so n still has its default value zero. Avoid overridable calls from constructors.",
     "jls-12.html#jls-12.5")
ask("assign-blank-final-on-every-path", ["Immutable object", "Constructor initialization"], "debug",
    "A class declares `private final int id;` and `Item(boolean named) { if (named) id = 1; }`. Why is the constructor rejected?",
    "The blank final field is not assigned on the path where named is false.",
    ["A final instance field can only be initialized at its declaration.",
     "A final int must always be assigned zero.",
     "A boolean parameter cannot control a constructor branch."],
    "Every normally completing constructor path must definitely assign a blank final instance field. Assign id in both branches, delegate appropriately, or reject the invalid path by throwing.",
    JLS + "jls-16.html")
ask("reject-invalid-construction", ["Data validation"], "design",
    "Range must always satisfy start <= end. Both endpoints are private final fields. Which constructor policy ensures that every successfully constructed Range satisfies its invariant?",
    "Check the endpoints and throw IllegalArgumentException if start > end.",
    ["Construct the invalid object and document that callers should check it later.",
     "Use assert alone, because assertions are always enabled in Java.",
     "Assign only start when the endpoints are invalid and return normally."],
    "A failed constructor does not return a successfully constructed Range to its caller. Assertions may be disabled, so they are unsuitable as the only public input check.",
    JLS + "jls-8.html#jls-8.8.7")
ask("instance-context-required", ["This reference", "Static state"], "debug",
    "Counter has an instance field n. Its `static int read() { return this.n; }` method fails to compile. If read is intended to report the receiver's own count, which change fits that intent?",
    "Make read an instance method and call it on a Counter object.",
    ["Replace this.n with Counter.n while leaving n as an instance field.",
     "Keep read static and replace this with super.",
     "Make n static so every Counter shares the same per-object count."],
    "A static method has no current object, so this is unavailable. An instance method supplies the receiver needed for per-object state.",
    JLS + "jls-8.html#jls-8.4.3.2")

group("Inheritance and method selection")
code("runtime-override-selection", ["Dynamic dispatch", "Upcasting"],
     "class Shape { String name() { return \"shape\"; } }\nclass Circle extends Shape { @Override String name() { return \"circle\"; } }",
     "Shape s = new Circle();\nSystem.out.print(s.name());",
     "circle", ["shape", "null", "Compilation fails because the variable is a Shape"],
     "The variable's type permits the call; the runtime Circle object determines which overriding instance method executes. Upcasting does not replace the object.",
     "jls-15.html#jls-15.12.4.4")
code("field-selection-versus-method-dispatch", ["Field hiding"],
     "class Base { int n = 1; int read() { return n; } }\nclass Child extends Base { int n = 2; @Override int read() { return n; } }",
     "Base b = new Child();\nSystem.out.print(b.n + \":\" + b.read());",
     "1:2", ["2:2", "1:1", "2:1"],
     "Field access b.n uses the declared Base type. The instance method call dispatches to Child.read, whose n refers to Child's field.",
     "jls-15.html#jls-15.11.1")
code("static-method-selection", ["Static method hiding"],
     "class Base { static String name() { return \"base\"; } }\nclass Child extends Base { static String name() { return \"child\"; } }",
     "Base b = new Child();\nSystem.out.print(b.name() + \":\" + Child.name());",
     "base:child", ["child:child", "base:base", "child:base"],
     "Static methods are hidden, not dynamically overridden. The Base-typed expression selects Base.name. Prefer class-qualified calls to make this selection explicit.",
     "jls-8.html#jls-8.4.8.2")
code("overload-uses-declared-argument-type", ["Overloading"],
     "class Printer {\n  static String show(Object x) { return \"object\"; }\n  static String show(String x) { return \"string\"; }\n}",
     "Object text = \"hello\";\nSystem.out.print(Printer.show(text));",
     "object", ["string", "hello", "Compilation fails because both overloads match"],
     "Overload resolution uses the expression's compile-time type, Object. Its runtime String value does not reselect a different overload.",
     "jls-15.html#jls-15.12.2")
ask("detect-misspelled-override", ["Override annotation"], "debug",
    "Base declares `void draw()`. Child accidentally declares `void Draw()`, expecting a replacement. Which change makes the compiler detect this mistake at the declaration?",
    "Add @Override to Draw(); compilation then reports that it overrides nothing.",
    ["Add @Deprecated; deprecated methods must match inherited signatures.",
     "Make Draw static; static methods automatically override instance methods.",
     "Make Draw final; final methods are required to override a superclass method."],
    "Java names are case-sensitive. @Override checks the intended relationship and exposes the typo before a caller silently inherits Base.draw.",
    JLS + "jls-9.html#jls-9.6.4.4")
ask("return-type-is-not-overload-key", ["Overloading"], "debug",
    "A class declares both `int size()` and `long size()` with method bodies. Why does compilation reject the pair?",
    "Return types alone cannot distinguish overloads with the same name and parameter types.",
    ["Java never permits both int and long results in one class.",
     "One method must be static to allow the identical parameter lists.",
     "The caller must cast the result before these declarations can compile."],
    "Method signatures distinguish parameter types, not return types. Rename a method or change its parameter list if the operations need to coexist.",
    JLS + "jls-8.html#jls-8.4.2")
ask("override-cannot-narrow-access", ["Overriding"], "debug",
    "Base has `public void save()`. Child declares `protected void save()` with @Override. Why is this invalid?",
    "An override cannot reduce the inherited method's accessibility.",
    ["A public method can never be overridden.",
     "Overriding requires the subclass method to be static.",
     "An override must change at least one parameter type."],
    "Clients permitted to call Base.save must remain able to call that operation through a Child. The override must remain public.",
    JLS + "jls-8.html#jls-8.4.8.3")
ask("override-checked-exception-bound", ["Overriding"], "apply",
    "Base declares `void load() throws java.io.IOException`. Which throws clause may an override use without broadening its checked-exception contract?",
    "`throws java.io.FileNotFoundException`",
    ["`throws Exception`", "`throws Throwable`", "`throws java.sql.SQLException`"],
    "FileNotFoundException is a subtype of IOException. An override may narrow or omit checked exceptions; it cannot add unrelated or broader checked exceptions.",
    JLS + "jls-8.html#jls-8.4.8.3")
ask("covariant-return-keeps-subtype", ["Covariant return"], "apply",
    "Base declares `Base copy()`. Child extends Base. Which declaration in Child is a valid override?",
    "`@Override Child copy() { return new Child(); }`",
    ["`@Override Object copy() { return new Object(); }`",
     "`@Override String copy() { return \"copy\"; }`",
     "`@Override void copy() { }`"],
    "Reference return types may be covariant: Child is a subtype of Base. Object is broader, String is unrelated, and void does not preserve the return contract.",
    JLS + "jls-8.html#jls-8.4.5")
ask("final-method-preserves-algorithm", ["Final method"], "design",
    "A base processor must always validate before saving. Subclasses may customize only the write step. Which API prevents an ordinary Java subclass from replacing the validate-then-write sequence?",
    "Use a final process() method that calls validation and a protected write() hook.",
    ["Make process protected but overridable and document the required order.",
     "Make process static and expect subclass dispatch for write().",
     "Expose validation as an optional public helper used by callers."],
    "A final instance method cannot be overridden. It can preserve the required sequence while an explicit hook provides the intended extension point.",
    JLS + "jls-8.html#jls-8.4.3.3")
ask("wrap-final-class", ["Final class", "Composition"], "design",
    "A library's final Token class exposes verify(). Your application needs to record a metric around verification. Which design works without changing the library?",
    "Create a wrapper containing a Token and delegate verify while recording the metric.",
    ["Extend Token and override verify.",
     "Create an anonymous subclass of Token to bypass final.",
     "Implement Token as though every final class were an interface."],
    "final forbids subclassing, including anonymous subclasses. A collaborator can still be held and called by a wrapper.",
    JLS + "jls-8.html#jls-8.1.1.2")
code("explicit-super-method-call", ["Inheritance", "Overriding"],
     "class Base { String label() { return \"B\"; } }\nclass Child extends Base {\n  @Override String label() { return super.label() + \"C\"; }\n}",
     "System.out.print(new Child().label());", "BC", ["B", "C", "CC"],
     "Child.label explicitly invokes Base.label using super, receives B, and appends C. That super call does not recurse into the override.",
     "jls-15.html#jls-15.12")

group("Contracts and object design")
ask("one-superclass-many-contracts", ["Single class inheritance", "Multiple interfaces"], "apply",
    "Worker is a class; Auditable and CloseableTask are interfaces. Which header gives Job Worker behavior and both interface contracts?",
    "`class Job extends Worker implements Auditable, CloseableTask`",
    ["`class Job extends Worker, Auditable, CloseableTask`",
     "`class Job implements Worker, Auditable, CloseableTask`",
     "`class Job extends Worker implements Auditable extends CloseableTask`"],
    "A class has at most one direct superclass and may implement multiple interfaces. The class follows extends; the interfaces follow implements.",
    JLS + "jls-8.html#jls-8.1")
ask("instantiate-concrete-abstraction", ["Abstract class", "Abstract method"], "debug",
    "`abstract class Shape { abstract double area(); }` and `class Circle extends Shape {}` are declared. The application needs a Circle instance. Which repair supplies a usable concrete implementation?",
    "Implement area() in Circle with a double result, then construct Circle.",
    ["Construct Shape instead; its abstract method will return zero.",
     "Mark Circle abstract and then instantiate Circle directly.",
     "Add a static area() method to Circle to implement the instance method."],
    "A concrete subclass must implement inherited abstract instance methods. Making Circle abstract would defer that obligation but would prevent direct construction.",
    JLS + "jls-8.html#jls-8.1.1.1")
ask("implement-public-interface-operation", ["Interface contract"], "debug",
    "`interface Drawable { void draw(); }` is implemented by `class Icon implements Drawable { void draw() {} }`. What must change?",
    "Declare Icon.draw public to implement the interface's public method.",
    ["Declare Icon.draw private because interface implementations are hidden.",
     "Remove implements; Icon will still be assignable to Drawable automatically.",
     "Make Icon.draw static to satisfy the interface instance method."],
    "The abstract interface method is implicitly public. An implementation cannot reduce its accessibility to package access.",
    JLS + "jls-9.html#jls-9.4")
ask("resolve-unrelated-defaults", ["Interface default method"], "debug",
    "Unrelated interfaces Left and Right each define `default String name()`. Both return different text. Class Both implements both. What resolves the inherited default-method conflict?",
    "Override name() in Both and explicitly choose or combine the implementations.",
    ["List Left first in implements so its default wins.",
     "Make Both final so Java can select the most specific default.",
     "Do nothing; Java picks the interface whose name sorts first."],
    "Unrelated defaults with the same signature require an explicit override. Inside it, Both may invoke Left.super.name() or Right.super.name().",
    JLS + "jls-9.html#jls-9.4.1.3")
code("class-method-beats-default", ["Interface default method", "Inheritance"],
     "interface Named { default String name() { return \"interface\"; } }\nclass Base { public String name() { return \"class\"; } }\nclass Child extends Base implements Named {}",
     "System.out.print(new Child().name());", "class",
     ["interface", "classinterface", "Compilation fails due to conflicting methods"],
     "The inherited concrete class method takes precedence over the interface default. This differs from a conflict between two unrelated interface defaults.",
     "jls-8.html#jls-8.4.8.4")
ask("qualify-interface-static-member", ["Interface static method"], "apply",
    "`interface Factory { static int version() { return 1; } }` and `class Tool implements Factory {}` are declared. Which invocation compiles?",
    "`Factory.version()`",
    ["`Tool.version()`", "`new Tool().version()`", "`((Factory) new Tool()).version()`"],
    "Interface static methods are called through their declaring interface. They are not inherited as class or instance methods by implementing classes.",
    JLS + "jls-9.html#jls-9.4.1")
ask("preserve-withdrawal-contract", ["Subclass substitutability", "Liskov contract"], "design",
    "Account.withdraw promises to accept any positive amount up to the current balance. A FixedTermAccount rejects every withdrawal before maturity. What is the problem when FixedTermAccount is passed to callers relying on Account's promise?",
    "The subtype strengthens the operation's preconditions; use a contract that represents its restricted capabilities.",
    ["The subtype is valid because throwing an unchecked exception always preserves a contract.",
     "The problem disappears if callers upcast FixedTermAccount to Account.",
     "Every subclass must store exactly the same fields as its superclass."],
    "Compilation alone does not guarantee behavioral substitutability. Callers accepting the base contract must not face new restrictions that the contract never allowed.",
    "https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf")
ask("delegate-changing-discount-policy", ["Composition", "Open-closed design"], "design",
    "Checkout has a switch over discount types. Every new discount requires editing Checkout, and the policy must be replaceable per request. Which design localizes future discount changes?",
    "Have Checkout call a DiscountPolicy collaborator and add implementations for new policies.",
    ["Add a subclass of Checkout for every combination of discount and payment type.",
     "Move the same expanding switch into one static method and keep adding branches.",
     "Store discount type as an int and let each caller implement the switch."],
    "A stable behavior contract lets Checkout delegate a varying decision. New policy implementations supply behavior without changing the checkout algorithm.",
    "https://martinfowler.com/articles/injection.html")
ask("inject-fake-through-abstraction", ["Dependency injection", "Dependency inversion"], "design",
    "Checkout currently constructs NetworkGateway inside charge(). Tests must simulate failures without network access. Which change provides that control while keeping production behavior available?",
    "Accept a PaymentGateway interface in Checkout's constructor and supply a fake in tests.",
    ["Make NetworkGateway a global static singleton shared by every test.",
     "Add a production boolean that skips all charging logic when tests run.",
     "Let Checkout construct a different concrete gateway by inspecting the test class name."],
    "The high-level operation depends on a contract and receives its collaborator. Production can supply the real gateway; tests control the same boundary with a fake.",
    "https://martinfowler.com/articles/injection.html")
code("iterate-polymorphic-elements", ["Polymorphic collection"],
     "interface Shape { int area(); }\nclass Square implements Shape { public int area() { return 4; } }\nclass Dot implements Shape { public int area() { return 1; } }",
     "List<Shape> shapes = List.of(new Square(), new Dot());\nint total = 0;\nfor (Shape shape : shapes) total += shape.area();\nSystem.out.print(total);",
     "5", ["8", "2", "0"],
     "Each element supplies its own implementation of area. One loop over the shared contract can combine results without tests for individual concrete classes.",
     "jls-15.html#jls-15.12.4.4")
ask("segregate-read-and-write-capabilities", ["Interface segregation"], "design",
    "ReadOnlyArchive implements Store, whose methods are read() and write(). It always throws UnsupportedOperationException from write(). Consumers that only read should not depend on writing. Which redesign expresses their actual needs?",
    "Split readable and writable contracts; let ReadOnlyArchive implement only the readable one.",
    ["Keep Store and have read-only clients call write once to discover support.",
     "Make write a default method that always throws for every implementation.",
     "Return null from write to hide unsupported operations."],
    "Separate capability contracts let clients request only the operations they use and avoid promising behavior an implementation cannot provide.",
    "https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf")
ask("separate-independent-change-reasons", ["Single responsibility"], "design",
    "InvoiceProcessor calculates tax, renders PDFs, and sends email. Tax rules, branding, and mail infrastructure change independently. Which decomposition reduces the number of unrelated changes in each class?",
    "Use a tax calculator, invoice renderer, and mail sender coordinated by the use case.",
    ["Keep one class but rename its methods calculate1, calculate2, and calculate3.",
     "Create one subclass per customer while leaving all three responsibilities in the base class.",
     "Replace all methods with static methods in the same class."],
    "The split follows independently changing responsibilities. Merely renaming methods, making them static, or subclassing per customer does not isolate those reasons to change.",
    "https://martinfowler.com/bliki/PresentationDomainDataLayering.html")
ask("shared-versus-owned-part-lifetimes", ["Association", "Aggregation", "Composition ownership"], "design",
    "A Team references existing Players who can move to other teams. An Order owns mutable LineItems that must not be shared with other orders. Which model fits these ownership rules?",
    "Teams reference independently managed Players; each Order controls its own LineItems and prevents shared mutable ownership.",
    ["Both containers must delete their referenced objects whenever the container is removed.",
     "Use inheritance: Team extends Player and Order extends LineItem.",
     "Share the same mutable LineItem among all Orders to enforce ownership."],
    "Association expresses a relationship; aggregation can describe independently existing parts, while composition models ownership. Java references do not enforce these domain lifetime rules automatically.",
    "https://www.omg.org/spec/UML/2.5.1/PDF")

group("Equality and safe object state")
code("logical-equality-versus-identity", ["Object equality"],
     "class Key {\n  final int id;\n  Key(int id) { this.id = id; }\n  @Override public boolean equals(Object other) {\n    return other instanceof Key && id == ((Key) other).id;\n  }\n  @Override public int hashCode() { return id; }\n}",
     "Key a = new Key(4);\nKey b = new Key(4);\nSystem.out.print((a == b) + \":\" + a.equals(b));",
     "false:true", ["true:true", "false:false", "true:false"],
     "Separate constructions create different identities. The supplied equals implementation compares the stored IDs, which are equal.",
     "jls-15.html#jls-15.21.3")
ask("equal-keys-need-consistent-hashes", ["Hash code contract"], "debug",
    "Key overrides equals to compare id but inherits Object.hashCode. A HashMap lookup using a separately created equal key is unreliable. Which repair restores the required contract?",
    "Override hashCode using the same equality-relevant state as equals.",
    ["Compare keys with == inside equals so distinct value keys always match.",
     "Generate a fresh random hash code on every call to spread keys evenly.",
     "Require unequal objects to always have unequal hash codes."],
    "Equal objects must have equal hash codes. Unequal objects may collide. A stable hash derived from equality-relevant state lets hash collections use equals correctly.",
    API + "java/lang/Object.html#hashCode()")
ask("mutable-key-after-insertion", ["Hash code contract", "Immutable object"], "design",
    "CustomerKey.equals and hashCode both use a mutable email field. A key's email is changed after insertion into a HashMap. Which design avoids invalidating the stored key's lookup behavior?",
    "Use an immutable key whose equality-relevant fields remain stable while it is stored.",
    ["Call hashCode once after each mutation so HashMap automatically relocates the entry.",
     "Make the map variable final so the keys cannot change.",
     "Override only equals; inherited identity hashes repair mutable keys."],
    "Changing a field used by hashing and equality can make the original entry unreachable by normal lookup. HashMap does not observe arbitrary mutations and reindex keys automatically.",
    API + "java/util/Map.html")
ask("equals-parameter-must-be-object", ["Object equality", "Override annotation"], "debug",
    "Key declares `public boolean equals(Key other)`, expecting HashSet to use it for logical equality. What is missing?",
    "Override equals(Object); equals(Key) is only an overload and does not replace Object.equals.",
    ["Make equals(Key) static so collections can call it without a receiver.",
     "Rename equals(Key) to hashCode(Key) to override both contracts.",
     "Make Key generic; collections only compare generic keys by value."],
    "Collections use the Object.equals contract. The more specific parameter introduces a different signature; @Override would expose that mistake. A matching hashCode is also required for equal values.",
    API + "java/lang/Object.html#equals(java.lang.Object)")
ask("redact-sensitive-representation", ["ToString representation"], "design",
    "A Credentials object contains a username and raw password. Logging a failed login prints the object. Which toString policy gives useful context without disclosing the password?",
    "Include an appropriate identifier and omit or redact the password.",
    ["Include every private field; private fields cannot appear in logs.",
     "Base64-encode the password so it is safe to print.",
     "Return the password only when the log level is debug."],
    "toString output can be copied into logs. Access modifiers do not protect text emitted by a method, and Base64 is reversible encoding.",
    API + "java/lang/Object.html#toString()")
code("final-reference-allows-mutation", ["Immutable object"],
     "", "final List<String> names = new ArrayList<>();\nnames.add(\"Ada\");\nSystem.out.print(names.size());",
     "1", ["0", "Compilation fails because names is final", "UnsupportedOperationException"],
     "final prevents assigning a different reference to names. It does not make the referenced ArrayList immutable or prohibit add.",
     "jls-4.html#jls-4.12.4")
ask("copy-input-and-protect-output", ["Defensive copying"], "design",
    "Roster receives a mutable List<String> and must expose a snapshot unaffected by later caller edits. Its accessor must also prevent edits to that snapshot. Null elements are forbidden. Which boundary policy meets both needs?",
    "Store List.copyOf(input) and return that unmodifiable list.",
    ["Store input directly and return Collections.unmodifiableList(input).",
     "Store a new ArrayList<>(input) and return that mutable stored list directly.",
     "Store input in a final field and return it directly."],
    "List.copyOf creates an unmodifiable snapshot of the supplied elements. A wrapper around the original list still observes changes through the original reference; a mutable returned copy used as internal storage exposes another mutation path.",
    API + "java/util/List.html#copyOf(java.util.Collection)")
ask("shallow-copy-keeps-mutable-elements", ["Defensive copying", "Immutable object"], "apply",
    "A Roster stores `List.copyOf(players)`. Player objects have a mutable score, and the caller retains references to them. Is the entire Roster deeply immutable?",
    "No; the list is unmodifiable, but the shared Player objects can still change.",
    ["Yes; List.copyOf recursively copies and freezes all element fields.",
     "Yes; a collection containing objects can never expose their mutations.",
     "No; List.copyOf always returns the same mutable list argument."],
    "Copying a collection copies element references, not an arbitrary object graph. Deeply stable observations require immutable elements or suitable element copies and controlled access.",
    API + "java/util/List.html#unmodifiable")
ask("record-component-is-shallowly-final", ["Immutable object", "Records"], "apply",
    "In Java 17, `record Team(List<String> names) {}` is constructed with a mutable ArrayList. The caller later adds a name to that same list. What happens to team.names()?",
    "It observes the addition; the generated record constructor stores the reference without a defensive copy.",
    ["It keeps the old contents because every record automatically deep-copies its components.",
     "The caller's add throws because creating a record freezes the list.",
     "The record declaration is illegal because records cannot contain lists."],
    "Record component fields are final, but final references do not freeze referenced objects. A compact constructor can replace names with List.copyOf(names) when a snapshot is required.",
    JLS + "jls-8.html#jls-8.10")

group("Nested types, functions, and generics")
ask("construct-static-nested-helper", ["Nested class"], "apply",
    "`class Outer { static class Helper {} }` is accessible to the caller. Which expression constructs Helper without an Outer instance?",
    "`new Outer.Helper()`",
    ["`new Outer().new Helper()`", "`Outer.new Helper()`", "`new Helper(Outer)`"],
    "A static nested class has no implicit enclosing Outer instance. Its qualified type name can be used directly in a construction expression.",
    JLS + "jls-8.html#jls-8.1.3")
ask("construct-inner-with-enclosing-instance", ["Inner class"], "apply",
    "`class Outer { class Inner {} }` is accessible, and `Outer outer = new Outer();` has run. Which expression associates a new Inner with outer?",
    "`outer.new Inner()`",
    ["`new Outer.Inner()`", "`Outer.new Inner()`", "`new Inner(outer)` from unrelated top-level code"],
    "This non-static member class needs an enclosing instance. A qualified instance-creation expression supplies outer as that instance.",
    JLS + "jls-15.html#jls-15.9.2")
code("lambda-this-versus-anonymous-this", ["Anonymous class", "Lambda target"],
     "class Demo {\n  String name = \"outer\";\n  void run() {\n    Runnable a = new Runnable() {\n      String name = \"inner\";\n      public void run() { System.out.print(this.name); }\n    };\n    Runnable b = () -> System.out.print(this.name);\n    a.run(); b.run();\n  }\n}",
     "new Demo().run();", "innerouter", ["outerouter", "innerinner", "outerinner"],
     "this in the anonymous class refers to that anonymous object. A lambda does not introduce its own this, so its this refers to the enclosing Demo.",
     "jls-15.html#jls-15.27.2")
ask("functional-interface-abstract-method-count", ["Lambda target"], "apply",
    "Which interface can be used as the target of `() -> 42`?",
    "`interface Value { int get(); default void reset() {} }`",
    ["`interface Value { int get(); void reset(); }`",
     "`interface Value { static int get() { return 42; } }`",
     "`interface Value { int get(int seed); }`"],
    "The target needs one compatible abstract method with no parameters and an int result. A default method does not add an abstract obligation; a static-only interface has no functional method.",
    JLS + "jls-9.html#jls-9.8")
ask("captured-local-must-be-effectively-final", ["Lambda target"], "debug",
    "Inside a method: `int count = 0; Runnable r = () -> System.out.print(count); count++;`. Why does this fail to compile?",
    "The captured local count is reassigned, so it is not effectively final.",
    ["A lambda can never read any local variable.",
     "Runnable.run must return the incremented count.",
     "Changing count after the lambda declaration is allowed only for int values."],
    "A captured local variable must be final or effectively final. The later increment breaks that requirement regardless of whether the lambda has run yet.",
    JLS + "jls-15.html#jls-15.27.2")
ask("unbound-method-reference-receiver", ["Method reference"], "apply",
    "Which java.util.function target type is compatible with `String::length`?",
    "`ToIntFunction<String>`",
    ["`IntSupplier`", "`Function<String, String>`", "`Supplier<String>`"],
    "The unbound instance method reference needs a String receiver as its input and produces an int. ToIntFunction<String>.applyAsInt has exactly that shape.",
    JLS + "jls-15.html#jls-15.13.2")
ask("reject-wrong-generic-element", ["Generics"], "debug",
    "`List<String> names = new ArrayList<>(); names.add(42);` fails to compile. What is the type-safe repair if the list must continue to contain only names as text?",
    "Convert the intended value to a String before adding it, or supply a valid String name.",
    ["Cast names to raw List and add the Integer through that reference.",
     "Cast the Integer object directly to String without conversion.",
     "Suppress unchecked warnings so every later element is guaranteed to be a String."],
    "List<String> accepts String values, not Integer values. Raw types and warning suppression can bypass checks but do not make the stored object a String.",
    JLS + "jls-4.html#jls-4.5")
ask("generic-invariance-protects-list", ["Inheritance and generics"], "apply",
    "Dog extends Animal. Why can't `List<Animal> animals = new ArrayList<Dog>();` compile?",
    "It would allow animals.add(new Animal()) to put a non-Dog into a list promised to contain Dogs.",
    ["A subclass object cannot ever be assigned to a superclass variable.",
     "ArrayList supports only final element classes.",
     "Java requires List and ArrayList to have identical class names."],
    "Generic types are invariant: List<Dog> is not List<Animal>. A suitable wildcard can offer a restricted view without allowing unsafe writes.",
    JLS + "jls-4.html#jls-4.10.2")
ask("extends-wildcard-restricts-writes", ["Inheritance and generics"], "apply",
    "Dog extends Animal. Given a mutable `List<? extends Animal> animals`, which operation is statically safe without casts?",
    "Read an element into an Animal variable.",
    ["Add a new Animal.", "Add a new Dog because every Dog is an Animal.", "Assign the list directly to List<Animal>."],
    "The unknown element type might be Dog, Cat, or another subtype. Reading yields an Animal, but adding a particular non-null subtype is unsafe because the actual element type is unknown.",
    JLS + "jls-4.html#jls-4.5.1")
ask("super-wildcard-permits-specific-input", ["Generics"], "apply",
    "Dog extends Animal. A method receives a mutable `List<? super Dog> destination`. Which operation is type-safe?",
    "Add a new Dog to destination.",
    ["Read every element directly into a Dog variable without a cast.",
     "Add a new Animal even when it is not a Dog.",
     "Assign destination directly to List<Dog>."],
    "The element type is Dog or one of its supertypes, so a Dog can be added. Reading provides only Object because the list may contain values of a broader supertype.",
    JLS + "jls-4.html#jls-4.5.1")
code("incompatible-downcast-fails-at-runtime", ["Downcasting"],
     "class Animal {}\nclass Dog extends Animal {}\nclass Cat extends Animal {}",
     "Animal animal = new Cat();\ntry {\n  Dog dog = (Dog) animal;\n  System.out.print(\"dog\");\n} catch (ClassCastException ex) {\n  System.out.print(\"bad cast\");\n}",
     "bad cast", ["dog", "null", "Compilation fails because all downcasts are illegal"],
     "The cast is statically permitted, but the runtime object is a Cat. A cast checks compatibility; it does not transform one object's class into another.",
     "jls-15.html#jls-15.16")
code("instanceof-null-is-false", ["Instanceof test"],
     "class Shape {}\nclass Circle extends Shape {}",
     "Shape shape = null;\nSystem.out.print(shape instanceof Circle);",
     "false", ["true", "NullPointerException", "Compilation fails because shape is null"],
     "instanceof evaluates to false for null. It does not dereference the value or claim that null is an instance of any class.",
     "jls-15.html#jls-15.20.2")
ask("sealed-direct-subclass-policy", ["Inheritance", "Sealed classes"], "apply",
    "In Java 17, `sealed class Shape permits Circle {}` and its direct subclass are in the same package of the unnamed module. Which Circle declaration completes a valid closed hierarchy?",
    "`final class Circle extends Shape {}`",
    ["`class Circle extends Shape {}` with no final, sealed, or non-sealed modifier",
     "`abstract class Circle extends Shape {}` with no final, sealed, or non-sealed modifier",
     "`final class Square extends Shape {}` instead of declaring the permitted Circle"],
    "An ordinary direct subclass of a sealed class must explicitly choose final, sealed, or non-sealed. final closes that branch; an unlisted subclass is not permitted.",
    JLS + "jls-8.html#jls-8.1.1.2")


def course():
    tests = [{"id": f"oop-medium-practice-{i + 1}", "title": title,
              "description": "Java 17 code reasoning and design decisions, with one learning outcome per question.",
              "difficulty": "medium", "questions": deepcopy(questions)}
             for i, (title, questions) in enumerate(GROUPS)]
    total = sum(len(test["questions"]) for test in tests)
    return {"schema_version": 1, "id": "oop-medium", "title": "Object-oriented Java — Medium",
            "description": f"{total} distinct Java 17 assessments covering object state, construction, dispatch, contracts, equality, and generics.",
            "subject": "Java OOP", "difficulty": "medium", "lessons": [], "tests": tests}
