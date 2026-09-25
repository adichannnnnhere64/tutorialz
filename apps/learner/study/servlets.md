## Understand

A servlet container maps requests to servlet instances. A typical instance handles concurrent requests, so request-specific values belong in local variables or request attributes, not mutable servlet fields. `ServletContext` is shared by the web application; `HttpSession` spans related requests and may itself be accessed concurrently.

Filters can validate, wrap or reject requests before passing them along with `chain.doFilter`. Sending an error is not a Java control-flow return: a rejecting filter must avoid continuing the chain. Set request encoding before parameters/body parsing when the applicable protocol requires it. A body stream is consumable; a logging/signature filter needs a bounded replayable wrapper if downstream code must read it again.

Lifecycle order matters: initialize application resources in a ServletContextListener when startup servlets depend on them. Release owned resources on shutdown. GET should not perform state-changing business operations.

## Apply

Filter fragment:

```java
if (!authorized(request)) {
    response.sendError(401);
    return;
}
chain.doFilter(request, response);
```

Here request/response are HTTP servlet types and `authorized` is the application's authentication decision. Use the correct status for the situation: authentication failure differs from an authenticated caller lacking permission. Ensure filter mappings and dispatcher types cover the relevant routes.

## Cheatsheet

| Concept | Remember |
| --- | --- |
| Forward | Server-side dispatch; request attributes remain available |
| Redirect | Client makes another request; request attributes are lost |
| Response commitment | Status and headers must be set before committing/flushing output |
| Multipart limits | `maxFileSize` limits a part; `maxRequestSize` includes the complete multipart request |
| Async processing | Requires async support in the servlet/filter chain; complete or dispatch the AsyncContext |
| Nonblocking output | Stop when `isReady()` is false; continue through readiness callbacks |
| Session fixation | Change session identifier on authentication; protect cookie attributes |

## Check yourself

A 5 MiB per-file limit accepts each of two 4.5 MiB files, but the total request limit is 8 MiB. Why is the upload rejected?

**Answer:** The complete request exceeds its total limit even though each part is individually below the file limit. Multipart framing also contributes to the request size.

## Sources

[Servlet 6.1 specification](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html) · [HttpServletRequest API](https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/http/HttpServletRequest.html)
