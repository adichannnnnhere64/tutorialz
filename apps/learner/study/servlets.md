## Understand

### The container owns servlet execution

A servlet is a container-managed component that processes requests through a lifecycle: construction and initialization, request service, and destruction. A servlet instance commonly handles concurrent requests. Instance fields therefore belong to the shared component, not to one request. Keep request-specific values in local variables or request attributes and make shared collaborators safe for concurrent use.

HttpServlet dispatches HTTP methods to operations such as doGet and doPost. The method name does not itself enforce business safety: a doGet implementation that deletes a record still violates HTTP expectations. The container supplies request and response objects with a defined lifetime. Do not store them in static fields or use them after completion. Passing them to arbitrary threads does not extend their legal lifetime.

This chapter targets Jakarta Servlet 6.0, using jakarta.servlet packages. Legacy javax.servlet applications need compatible dependencies and a migration strategy. Java SE javax packages such as javax.sql do not all change namespace. A package rename also does not upgrade a server's supported specification level; runtime compatibility must be checked independently.

### Filters, dispatchers, and wrappers

A filter can inspect or transform a request before calling the chain and inspect completion afterward. Not calling the chain deliberately short-circuits processing, which is useful for rejection but can accidentally suppress a response. Filters are mapped by URL or servlet and by dispatcher type. REQUEST, FORWARD, INCLUDE, ERROR, and ASYNC identify different dispatch paths.

A request wrapper or response wrapper decorates the container object. Wrapping is appropriate for narrowly changing behavior while preserving the rest of the contract. Reading the body in a logging filter consumes it unless the wrapper implements replay correctly. A simplistic wrapper can break multipart processing, nonblocking reads, character encoding, or large-body limits. Prefer tested infrastructure for complex transformations.

### Response commitment and session state

Headers and status can be changed before the response commits. Flushing or filling the buffer can commit it; after that, sending a redirect, resetting, or changing error handling may be too late. Choose content type and character encoding before obtaining the writer when they determine encoding. Do not mix getWriter and getOutputStream for the same response body.

HttpSession stores state associated with a client session, but multiple concurrent requests can use the same session. A session attribute containing a mutable cart is not automatically protected against racing updates. Authentication identity, session lifetime, and business data persistence are separate concerns. Session replication and failover are container-specific operational features, not guarantees implied merely by calling setAttribute.

## Apply

### Example V1: Keep request state local

Servlet 6.0 fragment; imports and container deployment are required.

```java
@jakarta.servlet.annotation.WebServlet("/hello")
public class HelloServlet extends jakarta.servlet.http.HttpServlet {
  @Override
  protected void doGet(jakarta.servlet.http.HttpServletRequest request,
                       jakarta.servlet.http.HttpServletResponse response)
      throws java.io.IOException {
    String name = request.getParameter("name");
    response.setContentType("text/plain");
    response.setCharacterEncoding("UTF-8");
    response.getWriter().print(name == null ? "Hello" : "Hello " + name);
  }
}
```

The name belongs to the invocation, so another request cannot replace it through a shared field. Plain-text output avoids treating the supplied name as HTML markup. This is not a general escaping utility: if the response were HTML, JavaScript, or a URL, context-appropriate encoding and input rules would be required. Add input-size limits for a real endpoint.

### Example V2: Understand a forward

Illustrative controller fragment before response commitment:

```java
request.setAttribute("order", orderView);
request.getRequestDispatcher("/WEB-INF/views/order.jsp")
       .forward(request, response);
```

The server dispatches the same request to a view, so its request attributes remain available and the browser does not initiate a new navigation merely because of the forward. A redirect instead instructs the client to make another request; ordinary request attributes do not carry over. Place implementation views under WEB-INF to prevent direct client access and enforce the controller path.

### Example V3: Follow asynchronous completion

Servlet 6.0 method-body fragment; the servlet and every applicable filter must support async. Error/timeout listeners and application logging are required for production use.

```java
jakarta.servlet.AsyncContext async = request.startAsync();
async.setTimeout(2000);
async.start(() -> {
  try {
    async.getResponse().setContentType("text/plain");
    async.getResponse().getWriter().write("ready");
  } catch (java.io.IOException failure) {
    getServletContext().log("Async response failed", failure);
  } finally {
    async.complete();
  }
});
```

StartAsync extends the request's processing lifecycle beyond the original service call. AsyncContext.start asks the container to run work; it is not proof that the work is nonblocking. The example does trivial work. Real operations must coordinate completion with timeout and error callbacks so races do not write or complete twice, and must stop or safely detach underlying work after the response ends.

### Example V4: Trace dispatcher-sensitive filters

Suppose an authentication filter is mapped only to REQUEST and a controller forwards to a protected internal resource. The forward has dispatcher type FORWARD, so that mapping does not cause the filter to run again. This may be intentional when authorization is already complete, or a gap if the internal resource relies on a check that never happened.

The solution is not blindly mapping every filter to every type. Determine the protected boundary and make dispatch behavior explicit. A logging filter mapped to both REQUEST and ASYNC can produce duplicate completion records if it assumes one invocation per browser request. Use a request-level correlation identifier and lifecycle-aware completion tracking.

## Advanced

### Asynchronous is not nonblocking

Asynchronous servlet processing releases the original request thread while keeping the request active. Nonblocking I/O uses ReadListener or WriteListener callbacks and readiness checks to avoid blocking while transferring data. These features address different resources. Moving a blocking database call to an async worker still consumes that worker and a database connection.

When writing nonblocking output, respect isReady and callback rules; do not busy-loop waiting for readiness. On input, process available data without assuming one callback contains the entire body. Handle partial reads, end-of-stream, and errors. Application processing may need its own bounded queue so fast network input does not overwhelm a slower downstream stage.

### Async dispatch and wrapper lifetime

AsyncContext.dispatch returns processing to a container dispatch path with dispatcher type ASYNC. This differs from RequestDispatcher.forward, including response-buffer behavior and async lifecycle rules. A dispatch or completion must follow the allowed state transitions; it is not safe to call them arbitrarily from multiple callbacks.

Wrappers passed into asynchronous processing may need to remain valid until that cycle finishes. A filter that releases its buffer immediately after the initial chain returns can corrupt later async output. Async listeners provide lifecycle hooks, but a listener may need re-registration for a newly started async cycle. Design wrapper ownership and cleanup against the actual request state machine, not just a synchronous try/finally mental model.

### Encoding, parameters, and multipart data

Set request character encoding before parameter parsing when the API and request type permit it. Once parameters have been read, changing encoding may be ineffective. Query-string decoding and request-body decoding can involve different container rules, so test non-ASCII values through the real server and proxy chain.

Multipart requests need configured limits and safe storage. Uploaded filenames are untrusted metadata, not safe filesystem paths. Generate storage names, reject unexpected content where appropriate, and avoid keeping unlimited data in memory. A declared content type does not prove file contents. Handle interrupted uploads and cleanup of temporary resources, including failure before the controller runs.

### Sessions, concurrency, and fixation

Rotate the session identifier after authentication according to the chosen security framework to reduce session-fixation risk. Configure cookies with appropriate Secure, HttpOnly, and SameSite behavior, and protect state-changing browser requests against CSRF. A cookie flag is one layer, not a replacement for authorization.

Concurrent session requests can race even when they arrive from one browser with multiple tabs. Synchronizing on a session object in one JVM is not a portable distributed-lock strategy across replicas. Put authoritative shared state in a service with suitable concurrency control, or use immutable/versioned session values with a defined conflict policy. Keep session payloads small and avoid storing live persistence contexts or request objects.

## Production

### Trace the full HTTP lifecycle

A useful request trace distinguishes arrival, filter processing, dispatch, service work, async handoff, response commitment, and final completion. Logging only the time spent inside the initial filter chain can underreport an asynchronous request's duration. Record safe route templates and correlation IDs, not raw secrets, cookies, or full request bodies by default.

Behind a reverse proxy, trust forwarded headers only from configured trusted infrastructure. Otherwise clients may spoof scheme, host, or remote address assumptions. Those values can influence redirects, secure-cookie decisions, and audit trails. Test deployment under its real context path and proxy configuration rather than only localhost at the root URL.

### Test adverse timing and capacity

Exercise concurrent requests against a shared session, slow clients, large bodies, client disconnects, async timeout races, error dispatches, and graceful shutdown. A client disconnect can occur after a business transaction commits but before the response is received, so retry behavior needs operation identity and idempotency where relevant.

Bound worker pools, queued async tasks, upload size, response buffering, and session counts. Async support is not unlimited capacity. Observe active requests, queued work, rejected submissions, and completion reasons. A timeout must have an owner responsible for releasing resources; returning an error page does not necessarily cancel a remote operation or free a database connection immediately.

## Exam reasoning

### Track scope and commitment

For state questions, ask whether a value lives in a method, request, session, servlet instance, or application context. Local request data is isolated; session and instance state may be shared. For navigation questions, distinguish server-side dispatch from a client redirect and determine which attributes and URL changes follow.

For response questions, mark the first operation that can commit output. A later attempt to forward or redirect may fail or be ineffective according to the API. For filter questions, inspect both URL mapping and dispatcher type. Do not assume every filter runs exactly once or on every internal dispatch.

For async questions, distinguish lifecycle extension from nonblocking transfer. Identify who completes the request, who handles timeout, whether wrappers remain valid, and what underlying work is cancelled. The best answer explains all relevant lifetimes rather than simply adding asyncSupported=true.

## Cheatsheet

| Topic | Remember |
| --- | --- |
| Servlet instance | Can serve concurrent requests; avoid request fields |
| Filter chain | Explicitly continue or intentionally short-circuit |
| Dispatcher type | REQUEST, FORWARD, INCLUDE, ERROR, ASYNC |
| Request wrapper | Preserve body, encoding, and lifecycle contracts |
| Forward | Same request, server dispatch, before commitment |
| Redirect | Client makes another request |
| Commit | Headers/status sent; reset options become restricted |
| Writer encoding | Choose before obtaining the writer |
| startAsync | Extend lifecycle; not automatic nonblocking I/O |
| ReadListener / WriteListener | Readiness-driven nonblocking transfer |
| Session attribute | Shared mutable value may still race |
| Upload filename | Untrusted metadata, never a trusted path |
| Proxy headers | Trust only configured proxy boundaries |

## Check yourself

### 1. Shared username

Why is a servlet field holding the current username unsafe?

**Answer:** Concurrent requests can overwrite the same field and leak or mix user state. Keep invocation data local or request-scoped.

### 2. Forward data

Does a request attribute survive a server forward?

**Answer:** Yes, it remains on the same request. It does not automatically survive a redirect because the client sends a new request.

### 3. Response timing

Can a servlet freely change response headers after flushing the writer?

**Answer:** No. Flushing can commit the response. Set status and headers before commitment and design error handling accordingly.

### 4. Advanced: async capacity

Does startAsync eliminate the need to bound database work?

**Answer:** No. It changes request-thread lifetime, not database capacity. Async work still needs bounded admission, deadlines, and resource cleanup.

### 5. Advanced: filter duplication

Why might one browser request produce two filter logs?

**Answer:** The filter may run for different dispatcher types, such as REQUEST and ASYNC, or an internal forward. Correlate dispatches and log true lifecycle completion deliberately.

### 6. Advanced: session replication

Does synchronizing on HttpSession guarantee cross-node cart consistency?

**Answer:** No. A local monitor does not coordinate separate JVMs or define replication conflict semantics. Use an authoritative concurrency strategy for shared business state.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta Servlet 6.0. Snippets require a matching container and appropriate mappings; async illustration is not a complete production endpoint.

- [Servlet 6.0 specification](https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0)
- [AsyncContext lifecycle](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/asynccontext)
- [ServletResponse commitment](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletresponse)
- [HttpServletRequest](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/http/httpservletrequest)
- [ReadListener](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/readlistener)
- [WriteListener](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/writelistener)
- [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP file upload controls](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
