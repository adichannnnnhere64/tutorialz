## Understand

JSP, now Jakarta Pages, is a server-side view technology translated into a servlet. Keep business operations in services/controllers and use the page to render a prepared model. Expression Language reads values, but `${value}` is not universal HTML escaping. Encode output for its exact context.

Page, request, session and application scopes have different lifetimes. A request attribute named `invoice` is available through `${requestScope.invoice}`. Request parameters are strings supplied by the client and are not trustworthy deployment metadata.

Place controller-only views under `WEB-INF`. Clients cannot directly request that path, but the controller can forward there after authorization. A redirect would ask the browser to request the protected path and fail.

## Apply

Jakarta Tags 3.0 JSP fragment:

```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<c:url value="/orders" var="ordersUrl" />
<a href="${ordersUrl}">Orders</a>
<p><c:out value="${requestScope.customerName}" /></p>
```

The URL tag accounts for the current context path; a literal `/orders` points at the server root. `c:out` escapes text for this ordinary HTML text context. Script, style and URL contexts need their own validation/encoding rules. Ensure the selected tag library is installed in the target runtime.

## Cheatsheet

| Mechanism | Purpose |
| --- | --- |
| `isErrorPage="true"` | Makes the implicit exception object available on an error page |
| `errorPage="..."` | Chooses a destination for this page's failures |
| `JspFragment.invoke(null)` | Evaluates a tag body using its current context writer |
| `<%@ include ... %>` | Translation-time inclusion |
| `<jsp:include ...>` | Request-time inclusion |
| `<c:forEach>` | Iterate over model values without embedding business logic |
| Pages 4.0 | Removes the `isThreadSafe` directive; adds ErrorData method/query metadata |

Do not keep per-user data in generated servlet instance fields. Removing `isThreadSafe` does not make existing shared mutable fields safe.

## Check yourself

Why can plain `${customerName}` create stored cross-site scripting in an HTML page?

**Answer:** Rendering untrusted text without the required context-specific encoding may let it become markup or script. Store valid data and encode when rendering it; HTML-text escaping is not interchangeable with JavaScript encoding.

## Sources

[Jakarta Pages 3.1](https://jakarta.ee/specifications/pages/3.1/) · [Jakarta Tags 3.0](https://jakarta.ee/specifications/tags/3.0/) · [Pages 4.0 changes](https://jakarta.ee/specifications/pages/4.0/)
