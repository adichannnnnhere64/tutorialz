## Understand

HTTP APIs expose resources and representations. A safe method should not request business-state mutation; an idempotent operation has the same intended effect when repeated. Idempotency does not require every repeated response to have the same status or body. GET is safe; PUT and DELETE have idempotent semantics; POST needs an explicit design for safe retries.

Jakarta REST, historically JAX-RS, maps paths and HTTP methods to resource methods. `@Consumes` describes accepted request media types and `@Produces` describes responses. A 415 concerns unsupported request content; 406 concerns an unacceptable response representation. JSON-B binds Java objects to JSON, while JSON-P supports JSON structures and streaming.

Separate persistence entities from externally versioned API representations. Validate input, authorize access to the specific resource and return a stable error shape without internal implementation details.

## Apply

Jakarta REST fragment:

```java
@Path("/invoices")
@Produces(MediaType.APPLICATION_JSON)
public class Invoices {
    @GET @Path("/{id}")
    public Response find(@PathParam("id") long id) {
        // Authorize this invoice, load a DTO, and build the response.
        return Response.status(Response.Status.NOT_FOUND).build();
    }
}
```

This stub deliberately returns 404; replace the body with an authorized lookup. Register the resource under the application's configured base path. Use exception mappers for consistent expected error responses, and apply request/response filters at the intended scope.

## Cheatsheet

| Concern | Design choice |
| --- | --- |
| Creation | Often 201 with a Location identifying the created resource |
| Accepted background work | 202 plus a way to query progress |
| Conditional update | ETag with `If-Match`; reject a stale version |
| Pagination | Bounded page size and stable ordering; consider cursors under concurrent writes |
| Client resilience | Connect/read timeouts, total budget and retries only when safe |
| Authentication vs authorization | Establish identity, then check permission for this operation/resource |
| Request/reply correlation | Trace ID is for observability; idempotency key is for effect deduplication |

## Check yourself

A client times out after creating an order. Should it blindly retry POST?

**Answer:** The server may already have committed. Use a stable idempotency key and stored result, or another explicitly designed retry contract, to avoid creating a second order.

## Sources

[Jakarta REST](https://jakarta.ee/specifications/restful-ws/4.0/) · [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110) · [JSON Binding](https://jakarta.ee/specifications/jsonb/3.0/)
