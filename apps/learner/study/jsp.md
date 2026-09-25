## Understand

### JSP is translated server code

Jakarta Server Pages, traditionally called JSP, renders server-side views. The container translates a page into a servlet implementation and compiles it, then executes that implementation to generate responses. A browser receives the generated output, not JSP directives or Java source. Translation can happen at deployment or on first use depending on tooling and configuration, so a page can fail before any application data is rendered.

This chapter uses Jakarta Pages 3.1, Expression Language 5.0, and Jakarta Tags 3.0 as its baseline. Legacy Java EE applications may use older javax packages, tag-library artifacts, and URIs. Do not mix namespace migration with an assumption that every historical page feature is the preferred design today. Learn scriptlet behavior for maintenance and exam reasoning, but use controllers, view models, EL, and tags for ordinary new view code.

A JSP declaration becomes part of the generated servlet class; a scriptlet becomes service-method code; an expression writes a value into the output. Their similar punctuation hides different scope and concurrency effects. A mutable field declared in a page can be shared by concurrent requests, just like a servlet field. Moving Java code into a page does not isolate it from normal Java threading rules.

### Keep presentation separate from business work

A controller should authorize the operation, load the required data, and prepare a bounded view model. The JSP should render that model. Database access, payment calls, and business transaction decisions in a page make errors, retries, and performance hard to control. A rendering failure after a business commit is not a reason to repeat the business operation automatically.

Put internal views under WEB-INF so clients cannot bypass controller preparation by requesting the page directly. A server forward preserves the request and its attributes, while a redirect causes a new request. Request scope is therefore appropriate for one rendered result. Session scope fits carefully chosen conversation state, and application scope is shared across users. Do not use a broad scope merely because it makes a missing value appear.

### EL evaluates; it does not universally escape

Expression Language resolves values and can navigate bean properties, maps, lists, and other supported objects. Explicit requestScope or sessionScope access reduces ambiguity when names overlap. Unqualified lookup follows scope-resolution rules; a name found in a broader scope can conceal an unexpectedly missing request attribute.

EL output is not automatic context-sensitive XSS prevention. Rendering user content into HTML text, an attribute, JavaScript, CSS, or a URL requires different handling. A value that looks harmless in a paragraph may break out of a script string. Prefer safe structured rendering and established context-aware encoders; do not invent a universal replace-angle-brackets function.

## Apply

### Example PAGES1: Render a request model safely

JSP fragment using Jakarta Tags 3.0. The controller supplies an order bean whose displayName is intended as plain HTML text.

```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<h1>Order</h1>
<p><c:out value="${requestScope.order.displayName}" /></p>
```

The tag's default XML escaping is useful in this HTML text position. It does not establish that the order belongs to the caller; authorization must happen before the view is selected. It also does not make the value safe for every JavaScript or URL context. The explicit requestScope avoids accidentally rendering a same-named session object.

If the model is absent, silently producing an empty fragment can hide a controller defect. Decide which attributes are required, validate them before dispatch, and test the view contract. Null-friendly presentation is useful for optional fields, not a reason to ignore missing required data.

### Example PAGES2: Iterate without a database query

JSP fragment; lines is a prepared, bounded request-scoped collection.

```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<ul>
  <c:forEach items="${requestScope.lines}" var="line" varStatus="position">
    <li><c:out value="${position.count}" />:
        <c:out value="${line.label}" /></li>
  </c:forEach>
</ul>
```

VarStatus supplies iteration metadata; count is one-based while index is zero-based. The page traverses prepared data instead of querying per row. If line.label is a lazy ORM property, accessing it may still trigger database work or fail after the persistence context closes. Use an explicit projection so the view's cost is predictable and independent of persistence lifetime.

### Example PAGES3: Choose include semantics

Translation-time inclusion:

```jsp
<%@ include file="/WEB-INF/fragments/legal.jspf" %>
```

Request-time inclusion:

```jsp
<jsp:include page="/WEB-INF/views/sidebar.jsp" />
```

The directive contributes source to the translated page, so declarations and directives can interact during translation. The action executes the target during request processing and includes its output. The included resource does not freely replace the surrounding response's status and headers. Choose based on lifecycle and composition requirements, not on which syntax is shorter.

A static legal fragment is a reasonable directive use. A sidebar whose output depends on current request data may fit request-time inclusion, but data loading should still be controlled by application design. Neither mechanism makes an included file a security boundary; the caller and target must agree on authorization and model assumptions.

### Example PAGES4: Make scope collisions visible

Suppose a controller sets request attribute title to Order details while a session also contains title with Last search. An unqualified EL title resolves the nearer request value. If a later code path forgets to populate the request attribute, the session value may become visible instead of an obvious failure.

Use explicit scope access for important model values and avoid generic shared attribute names. The diagnosis is to inspect every controller branch and scope lifetime, not to copy the session value into application scope. A wider scope would make the accidental state sharing worse.

## Advanced

### Translation lifecycle and concurrency

Translation errors include invalid directives, unresolved tag libraries, malformed expressions, and generated Java compilation failures. Runtime errors occur after the page implementation exists, such as a property accessor throwing an exception. Diagnose the phase first: changing request data will not repair a missing tag library during translation.

JspInit and jspDestroy participate in page lifecycle, while the generated service method handles requests. A declaration of a reusable mutable formatter or counter can create shared state. Prefer immutable helpers or properly scoped components. Generated servlet source can be useful during diagnosis, but do not edit generated files as the durable fix; correct the page or build configuration.

### EL property rules and coercion

Property access may call getters and therefore execute application code. A getter with network I/O, mutation, or hidden queries makes rendering unpredictable. Design view models with inexpensive, side-effect-free accessors. A property name is not always a direct Java field access, and missing-property behavior depends on the resolver and target type.

EL has its own coercion and operator rules. Do not assume a Java expression copied into EL has identical semantics, especially for null, empty values, numeric conversion, and string concatenation. The empty operator handles defined empty cases, but it does not validate a complex business object. Test values such as missing attributes, empty collections, zero amounts, and localized text instead of only a fully populated happy path.

### Tags, tag files, and reusable views

Standard tags provide conditionals, iteration, formatting, and other view operations. Custom tags or tag files encapsulate reusable presentation behavior with declared attributes. Keep their contracts small: input model, optional body, output context, and error behavior. A tag that secretly opens a database connection or changes authentication state is difficult to reuse safely.

Tag handler instances may be managed and reused according to their lifecycle contracts. Do not retain request-specific data across invocations unintentionally. Release references and reset state as required by the chosen handler API. Tag files can reduce Java boilerplate, but they still execute within the page/container model and must follow the same output-encoding and scope discipline.

### Error pages, buffering, and escaping contexts

An error page can render an exception-oriented view when configured appropriately, but the response may already be committed. Once substantial output has been flushed, switching to a clean error response is constrained. Prepare risky operations before rendering, keep rendering lightweight, and log a correlation ID rather than exposing raw stack traces.

Escaping is output-context specific. C:out is useful for text, not a complete JavaScript serializer. URLs need allowed schemes and destinations in addition to encoding; an encoded unsafe scheme can still be unsafe. Rich HTML supplied by users needs a trusted sanitizer with an explicit policy, not merely disabling escaping. Content Security Policy adds defense in depth but does not repair unsafe template construction.

## Production

### Precompile and exercise real pages

Precompilation catches many translation errors before users reach a page. Still run integration tests in a matching container because tag libraries, class loading, expression resolution, and deployment descriptors influence behavior. Test non-ASCII text, missing optional fields, long values, authorization failures, and empty result sets. A controller unit test that returns the correct view name does not prove the JSP renders successfully.

Measure rendering latency and query counts. A table of fifty rows can trigger fifty lazy loads if each getter consults persistence. Large output buffering can consume memory, while premature flushing restricts error handling. Set deliberate limits and paginate prepared data. Avoid placing sensitive model values in hidden fields merely because they are not visibly rendered; clients can inspect all delivered HTML.

### Migrate legacy pages deliberately

Inventory scriptlets, declarations, tag-library versions, custom handlers, EL assumptions, and javax imports before migration. Replace business logic with services and view models incrementally while preserving observable behavior. Verify that the target server supports the chosen Pages, Tags, and EL versions and that application packaging does not duplicate incompatible APIs.

Modernizing a view layer does not require rewriting every page at once. Establish safe model and encoding conventions, add regression tests around important pages, and move risky shared state out first. If choosing a different rendering technology, keep authorization and business rules outside the templates so the migration changes presentation rather than silently changing domain behavior.

## Exam reasoning

### Identify phase, scope, and output context

For syntax questions, distinguish a directive, declaration, scriptlet, expression, EL expression, and standard action. Ask whether it affects translation, class-level state, request execution, or output. Similar-looking delimiters can place code in very different lifetimes.

For data questions, trace scope resolution and whether navigation is a forward or redirect. For include questions, distinguish translated source composition from request-time execution. For security questions, identify the exact output context before selecting an escaping mechanism. “EL is safe because it is not a scriptlet” is not a valid security argument.

For migration questions, separate API namespace changes from tag-library resolution and server compatibility. A page that compiles may still expose incorrect data or trigger hidden queries. The strongest answer preserves the controller/view boundary, predictable rendering cost, and context-appropriate output handling.

## Cheatsheet

| Topic | Precise meaning |
| --- | --- |
| JSP translation | Page becomes a servlet implementation |
| Declaration | Generated class member; mutable state can be shared |
| Scriptlet | Java in request processing; avoid business logic here |
| EL | Property resolution and coercion, not universal escaping |
| requestScope | One request, including an internal forward |
| sessionScope | Client conversation; concurrent requests can share it |
| applicationScope | Shared application state |
| c:out | Escapes XML-sensitive text by default |
| c:forEach | Iterate prepared data; inspect getter side effects |
| Include directive | Translation-time source composition |
| jsp:include | Request-time output inclusion |
| WEB-INF views | Prevent direct client access to internal views |
| Error view | Limited once response output commits |
| Migration | Align Pages, EL, Tags, container, and namespaces |

## Check yourself

### 1. Browser visibility

Does the browser execute a JSP scriptlet?

**Answer:** No. The server translates and executes the page. The browser receives generated output, such as HTML, not the original server-side Java code.

### 2. Shared counter

Why can a counter in a JSP declaration race?

**Answer:** It becomes generated servlet instance state and may be accessed by concurrent requests. A page declaration does not create a separate field per request.

### 3. Include timing

Which inclusion mechanism combines source during translation?

**Answer:** The include directive. Jsp:include executes the target during request processing and incorporates its output instead.

### 4. Advanced: misleading scope

Why can a missing request title unexpectedly show an old value?

**Answer:** Unqualified resolution may find a same-named value in a broader scope such as session. Use explicit scope and validate the required controller-to-view model.

### 5. Advanced: escaping boundary

Is c:out sufficient for inserting arbitrary text into a JavaScript string?

**Answer:** No. XML/HTML text escaping is not JavaScript-context encoding. Prefer safe serialization or avoid injecting untrusted data into executable contexts.

### 6. Advanced: hidden database work

A controller performs one query, but rendering performs fifty more. What should be inspected?

**Answer:** Lazy properties and side-effecting getters used by the view. Prepare an explicit bounded projection and test rendering query counts instead of extending persistence lifetime without analysis.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta Pages 3.1, EL 5.0, Tags 3.0. JSP fragments require a matching container and prepared model.

- [Jakarta Pages 3.1 specification](https://jakarta.ee/specifications/pages/3.1/jakarta-server-pages-spec-3.1)
- [Jakarta Tags 3.0 specification](https://jakarta.ee/specifications/tags/3.0/jakarta-tags-spec-3.0)
- [Jakarta Expression Language 5.0](https://jakarta.ee/specifications/expression-language/5.0/)
- [Pages API](https://jakarta.ee/specifications/pages/3.1/apidocs/)
- [Servlet dispatch and response lifecycle](https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0)
- [OWASP XSS prevention contexts](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP content security policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
