## Understand

### Resources and representations

An HTTP API exposes resources through representations and operations with defined semantics. A resource is the conceptual thing, such as an order; JSON is one representation of its state. A URL is not a permission token. Authentication establishes a caller identity, while authorization decides which resource and operation that caller may access. Keep those checks independent from routing and serialization.

Jakarta RESTful Web Services 3.1 provides annotations, providers, filters, interceptors, asynchronous facilities, and client APIs for implementing HTTP services. It does not automatically make an API's business model consistent or its operations idempotent. This chapter combines Jakarta REST 3.1 with HTTP semantics from RFC 9110, caching from RFC 9111, and problem details from RFC 9457.

### Safe, idempotent, and repeatable are different

A safe method requests essentially read-only semantics from the client's perspective. Incidental logging can still occur, but GET should not be used to perform an intended deletion or purchase. An idempotent method has the same intended effect when repeated as when applied once. Responses need not be identical: repeating DELETE can return a different status after the resource is gone while preserving its intended effect.

PUT and DELETE have idempotent semantics; POST does not promise idempotency by default. An application can design a POST operation with an idempotency key, but the server must implement the durable contract. A header name alone prevents nothing. PATCH semantics depend on the patch document and operation; incrementing a field is not equivalent to setting it to a particular value.

### Status, headers, and bodies form one contract

Use status codes to describe the outcome and headers to carry protocol metadata. A successful creation commonly uses 201 with a Location identifying the created resource. An accepted asynchronous job can use 202 with a way to inspect progress; 202 is not proof the job completed. A 204 response has no content. Avoid returning 200 with an error-shaped body for every failure because intermediaries and clients then lose useful semantics.

Content-Type describes the representation being sent. Accept expresses acceptable response representations. Unsupported request media type and unacceptable response representation are different problems, commonly associated with 415 and 406 respectively. Do not infer format solely from a filename extension or assume JSON parsing validates business meaning.

## Apply

### Example R1: Declare a resource boundary

Jakarta REST 3.1 fragment; OrderService and OrderView are application types, with CDI integration supplied by the runtime.

```java
@jakarta.ws.rs.Path("/orders")
@jakarta.ws.rs.Produces(jakarta.ws.rs.core.MediaType.APPLICATION_JSON)
public class OrdersResource {
  @jakarta.inject.Inject
  OrderService service;

  @jakarta.ws.rs.GET
  @jakarta.ws.rs.Path("/{id}")
  public OrderView find(@jakarta.ws.rs.PathParam("id") long id) {
    return service.findVisibleOrder(id);
  }
}
```

The service must enforce object-level and tenant authorization. The resource should return a deliberate projection rather than an entity exposing internal fields. Provider configuration determines JSON binding, and exception mapping determines errors. Compilation against the API alone does not prove those runtime providers are installed.

### Example R2: Prevent a lost update

Illustrative HTTP exchange. The server previously returned a strong entity tag for the current order representation.

```http
PUT /orders/42 HTTP/1.1
Content-Type: application/json
If-Match: "order-42-v7"

{"deliveryNote":"Leave at reception"}
```

The server applies the update only if the precondition still matches the current representation according to its contract. A stale validator normally produces 412 Precondition Failed. The comparison and update must be protected atomically at the authoritative store, for example using a version predicate. Checking an ETag in application memory and then blindly updating later still permits a race.

This payload illustrates the concurrency header, not a universal order schema. A PUT contract must define the complete intended representation or the resource being replaced; use an appropriate partial-update contract if only one property is being changed. The endpoint must also authorize the caller before exposing or modifying the resource.

### Example R3: Revalidate a cached representation

Illustrative conditional retrieval:

```http
GET /catalog/summary HTTP/1.1
If-None-Match: "catalog-v12"
```

If the selected representation still matches the validator and the request conditions are satisfied, the server can return 304 without resending its content. The client uses its stored representation. If the representation changed, the server sends the new content and validator. Cache-control policy still determines storage and freshness; an ETag alone does not specify how long a cache may reuse data without validation.

### Example R4: Retry a payment with an application key

A client creates a random operation key for one payment attempt and retains it across transport retries. The server scopes that key to the authenticated tenant and operation, stores a request fingerprint, and atomically records the resulting business effect and replayable outcome.

If the same key and same request arrive again, the server returns the recorded outcome according to its contract. If the same key is reused with a different amount, it rejects the conflict. Concurrent duplicates must converge on one authoritative operation, not both pass a cache lookup and charge independently. Define retention, in-progress responses, and recovery from uncertain external payment outcomes.

## Advanced

### Conditional requests and representation identity

Strong validators indicate byte-level equivalence for relevant representation comparisons; weak validators express weaker equivalence and are not interchangeable for every precondition. If-Match uses strong comparison. Representation variants matter: compressed and uncompressed or language-specific responses may need distinct validators and Vary metadata according to the implementation.

Conditional writes connect HTTP optimistic concurrency to database concurrency. The resource's version, tenant, and identity need a coherent mapping. A version number used only in a response header but ignored during persistence is decoration, not protection. If the server requires preconditions, document that policy and the missing-precondition response separately from a stale-precondition failure.

### Cache controls and privacy

No-store instructs caches not to store the response. No-cache permits storage but requires validation before reuse under its rules. Private restricts shared-cache storage; it is not encryption. Public caching of personalized responses can leak data if cache keys omit authorization-relevant variation. Avoid solving this by placing raw bearer tokens in logs or cache keys visible to operators.

Vary identifies request-header dimensions used to select a representation. Excessive variation can destroy cache effectiveness, while missing variation can serve the wrong representation. Application caches also need tenant-aware keys and invalidation rules; HTTP cache headers do not configure every internal cache automatically. Consider error and redirect caching behavior, not only successful GET responses.

### Pagination, sorting, and consistency

Offset pagination is simple but can become expensive and unstable as rows are inserted or removed between requests. Keyset pagination advances from a stable ordered position and often scales better, but requires a deterministic sort with a unique tie-breaker. A cursor should encode or reference the sort/filter context and be validated; treating arbitrary client cursor text as trusted SQL is unsafe.

Define whether a multi-page traversal is a live view or a consistent snapshot. Neither pagination style alone freezes a changing dataset. Bound page size, sort options, filters, and total work. Include authorization in every page query, not only the first request. An opaque cursor is an implementation abstraction, not automatically a security boundary.

### Error contracts and evolution

Problem details provide a standard-shaped error representation with fields such as type, title, status, detail, and instance. Use stable problem types and safe extension fields for machine action. Do not expose stack traces, database schema, or secrets in detail. Clients should not parse a localized human message to decide whether a retry is safe.

Evolve schemas with compatibility tests. Adding an optional field is often compatible, but strict clients, enum handling, required-field changes, and semantic changes can break consumers. Renaming a field or changing units is not harmless because the JSON still parses. Version the contract where needed and document deprecation, overlap, and migration rather than multiplying versions without ownership.

## Production

### Retry within a budget

Retry only when the operation's semantics and failure classification permit it. A timeout after sending a request leaves the outcome uncertain; the server may have committed. Use idempotency or reconciliation for side-effecting operations. Bound total attempts and elapsed time, apply backoff and jitter, and respect appropriate Retry-After guidance.

Do not layer uncontrolled retries in the HTTP client, service, gateway, and job runner. Three attempts at each of four layers can amplify one request into many calls. Choose a retry owner and propagate the deadline. Circuit breakers and bulkheads control failure spread but do not decide whether a repeated payment is correct.

### Test protocol behavior, not only JSON

Integration tests should check status codes, headers, content negotiation, authentication, object authorization, caching, conditional updates, malformed input, and size limits. Test concurrent updates using the same ETag and concurrent duplicate idempotency keys. Verify response bodies are absent where required and that error representations remain safe.

Manage Jakarta REST clients as resources with appropriate reuse and closure. Configure connection, read, and overall deadlines according to the implementation, and do not assume every timeout cancels remote work. Observe route-level latency, status classes, retry counts, and dependency errors with bounded labels. Avoid logging full tokens, payment details, or arbitrary request bodies.

## Exam reasoning

### Start with intended effect

For method questions, ask what effect the client requests and what happens if the request is repeated. Idempotent does not mean identical responses or no side effects of any kind. Safe does not mean authorized for every user. POST can support an application idempotency contract, but the contract must be implemented rather than inferred.

For cache questions, distinguish storage, freshness, and validation. For conditional updates, separate missing, matching, and stale validators and identify the atomic persistence boundary. For status questions, separate creation, acceptance, completion without content, malformed input, and authorization failure.

For architecture questions, follow uncertainty: the client timed out, but did the server commit? Which identifier lets the system determine that later? A robust answer includes retry and reconciliation semantics rather than simply increasing a timeout or adding a generic retry annotation.

## Cheatsheet

| Topic | Precise contract |
| --- | --- |
| GET | Safe retrieval semantics; no intended mutation |
| PUT / DELETE | Idempotent intended effect, not identical response |
| POST | No default idempotency promise |
| Content-Type / Accept | Sent representation / acceptable response |
| 201 / 202 / 204 | Created / accepted / successful without content |
| If-Match | Conditional write with strong comparison |
| If-None-Match | Revalidation or conditional creation according to method |
| 304 | Reuse stored representation; no new response content |
| no-cache / no-store | Validate before reuse / do not store |
| Vary | Representation selection dimensions |
| Cursor pagination | Stable sort, validation, authorization on every page |
| Problem details | Stable machine contract, safe human detail |
| Idempotency key | Durable scoped deduplication and request consistency |
| Retry | Bounded, semantically safe, deadline-aware |

## Check yourself

### 1. Repeated delete

Can DELETE remain idempotent if the first response is 204 and the next is 404?

**Answer:** Yes. Idempotency concerns the intended effect, not identical response codes. The resource remains absent.

### 2. Cache instruction

Does no-cache mean a response must never be stored?

**Answer:** No. It generally requires validation before reuse. No-store expresses the instruction not to store.

### 3. Accepted work

Does 202 prove a background import finished successfully?

**Answer:** No. It indicates acceptance for processing. Provide a way to inspect eventual status and document failure behavior.

### 4. Advanced: ETag race

Why is checking a version and then issuing an unconditional update insufficient?

**Answer:** Another transaction can change the resource between those steps. Make the version check and update atomic at the authoritative store.

### 5. Advanced: key reuse

What should happen if one idempotency key is reused for two different payment amounts?

**Answer:** Reject the conflict according to the API contract. Replaying or silently accepting a different request would make the key's meaning ambiguous and unsafe.

### 6. Advanced: pagination drift

Does keyset pagination automatically give a frozen snapshot across ten requests?

**Answer:** No. It defines an advancement strategy, not snapshot isolation across requests. The API must separately define and implement its consistency model.

## Sources

Reviewed 2026-09-25. Baselines: Jakarta REST 3.1 and the named HTTP RFCs. Idempotency-key workflow is an application design example, not a claim of universal header semantics.

- [HTTP semantics, RFC 9110](https://httpwg.org/specs/rfc9110.html)
- [HTTP caching, RFC 9111](https://httpwg.org/specs/rfc9111.html)
- [Problem details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
- [Jakarta REST 3.1 specification](https://jakarta.ee/specifications/restful-ws/3.1/jakarta-restful-ws-spec-3.1)
- [Jakarta REST API](https://jakarta.ee/specifications/restful-ws/3.1/apidocs/)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [PostgreSQL pagination ordering](https://www.postgresql.org/docs/17/queries-limit.html)
