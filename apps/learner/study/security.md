## Understand

Authentication establishes who is calling. Authorization decides what that identity may do to a particular resource. A logged-in user is not necessarily allowed to read another tenant's invoice. Perform checks on trusted server-side data at the business boundary, not only by hiding buttons.

Jakarta Bean Validation expresses structural and domain constraints. `@NotNull`, `@Size`, `@Min`, `@Email` and composed/custom constraints serve different purposes. Many constraints allow null so they can be combined with `@NotNull`; read each constraint's contract. `@Valid` cascades validation into nested objects. Groups select constraints for a workflow, while a class-level validator can check relationships between fields.

Validation and authorization are independent. A syntactically valid request may still be forbidden. Database constraints protect invariants against concurrent requests and alternative writers even when application validation is correct.

## Apply

Bean Validation fragment:

```java
record CreateInvoice(
    @NotNull @Positive java.math.BigDecimal total,
    @NotBlank String customerId
) {}
```

Assume a compatible Jakarta validation provider and validation at the entry point. A service still verifies that the caller may invoice the customer. A database uniqueness constraint can enforce an external invoice key; catching the resulting conflict requires a defined API/business response.

## Cheatsheet

| Threat / concern | Control |
| --- | --- |
| SQL injection | Bind parameter values; allowlist dynamic identifiers |
| XSS | Context-specific output encoding; validate allowed markup separately |
| CSRF | Protect cookie-authenticated state changes with an appropriate CSRF strategy |
| Session fixation | Rotate session identifier on successful authentication |
| Secrets | Managed configuration, restricted access, rotation; never log credentials |
| Transport | TLS with certificate validation |
| Authorization | Least privilege, role mappings, resource ownership and tenant isolation |
| Auditability | Actor, action, outcome, correlation; avoid sensitive payloads |

## Check yourself

Why is a unique database constraint still needed after a service checks that an invoice key is unused?

**Answer:** Two transactions can both observe absence before either inserts. The database constraint arbitrates the invariant under concurrency; the application must handle the losing operation's conflict.

## Sources

[Jakarta Validation](https://jakarta.ee/specifications/bean-validation/3.1/) · [Jakarta Security](https://jakarta.ee/specifications/security/4.0/) · [OWASP prevention guides](https://cheatsheetseries.owasp.org/)
