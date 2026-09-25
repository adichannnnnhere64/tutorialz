## Understand

### Identity is not permission

Authentication establishes an identity or verifies a credential. Authorization decides whether that identity may perform an operation on a particular resource in its current state. A valid login does not authorize every invoice, tenant, administrative action, or refund. Enforce access rules on the server at every relevant boundary, including background jobs and message consumers, rather than relying on hidden interface buttons.

Roles and groups are related but distinct. An identity store may provide group membership, while the application declares roles that map to permissions. The deployment must map those concepts deliberately. A role such as support-agent may permit viewing some account data but not changing bank details. Object ownership, tenant, amount, workflow state, and separation-of-duties rules often require checks beyond a simple role annotation.

Jakarta Security 3.0 supplies mechanisms for authentication integration, identity stores, caller information, and role checks in the Jakarta environment. It does not invent the application's domain policy. This chapter also uses OAuth/OIDC standards and OWASP defensive guidance. Security configuration is version-sensitive; production choices must be checked against the actual framework and identity provider.

### OAuth, OIDC, and token meaning

OAuth 2.0 is an authorization framework for delegated access. OpenID Connect, or OIDC, adds an identity layer with an ID token and authentication-related behavior. An access token is intended for a resource server; an ID token is intended for the client to understand authentication. Do not interchange them merely because both happen to be JWTs.

A JWT is a structured token format. A signed JWT is not automatically encrypted: its claims can often be decoded by anyone holding it. Base64url decoding is not signature verification. A resource server must validate the token according to its trusted issuer contract, including acceptable algorithms, signature keys, issuer, audience, expiry, and relevant not-before constraints. A token valid for another service is not valid for this service just because the signature verifies.

### Browser boundaries are different controls

CSRF abuses credentials that a browser automatically attaches to a request, such as cookies. XSS executes attacker-controlled script in an application's origin. CORS controls browser cross-origin access to responses; it is not a general authentication or server-to-server access-control mechanism. These threats overlap but cannot be solved by treating their acronyms as interchangeable configuration flags.

Cookie Secure and HttpOnly settings protect different aspects of transport and script access. SameSite reduces some cross-site request behavior but needs an application-specific policy and is not a universal replacement for CSRF defenses. A bearer token stored in a cookie can still create a CSRF-relevant authentication model. A bearer token accessible to injected JavaScript can be stolen by XSS.

## Apply

### Example SEC1: Scope an object lookup

Illustrative authorized query pattern:

```sql
SELECT invoice_id, total
FROM invoice
WHERE tenant_id = ? AND invoice_id = ?;
```

The server derives the tenant from validated identity and authorization context, not an arbitrary request parameter. It also verifies that the caller's role and relationship permit the requested operation. Including the tenant predicate prevents an accidental cross-tenant lookup, but it does not by itself express every object-level rule.

The same boundary belongs in cache keys, background job payload handling, exports, and search indexes. If a cache uses only invoice ID, correctly scoped SQL can still be bypassed by returning another tenant's cached result. Test the entire read path, not only the database query.

### Example SEC2: Reject the wrong token audience

A token has a valid signature from the trusted issuer and has not expired, but its audience is payroll-api. The receiving service is inventory-api. The correct decision is rejection unless the explicitly configured token contract legitimately includes inventory-api.

Do not repair this by ignoring audience validation or accepting any token the identity provider signs. The issuer may sign tokens for many clients and services with different purposes. Configure the expected issuer and audience on the server, and resolve keys only through trusted metadata. A token's key identifier is a lookup hint, not permission to fetch arbitrary attacker-chosen URLs.

### Example SEC3: Keep values out of SQL syntax

JDBC fragment; connection, tenant, and displayName are supplied by an authorized application operation.

```java
try (java.sql.PreparedStatement statement = connection.prepareStatement(
    "select customer_id from customer where tenant_id = ? and display_name = ?")) {
  statement.setString(1, tenant);
  statement.setString(2, displayName);
  try (java.sql.ResultSet rows = statement.executeQuery()) {
    while (rows.next()) consume(rows.getLong(1));
  }
}
```

Parameterization separates values from SQL syntax. It does not authorize the query, bound its cost, or safely substitute arbitrary identifiers. If the user chooses sort order, map an allowed symbolic choice to a fixed SQL fragment. Avoid building raw SQL from names, filters, or JSON paths without a documented safe construction method.

### Example SEC4: Protect a cookie-authenticated transfer

A browser application posts a transfer using a session cookie. The server requires a valid session, verifies a CSRF token bound to that session or the framework's supported equivalent, validates the recipient and amount, and enforces account ownership and transfer policy. It records a stable operation ID for retries and audit.

CORS configuration alone is insufficient because cross-site requests can reach a server even when the browser will not expose the response to the attacker. Authentication alone is insufficient because the browser may attach the victim's cookie. CSRF protection alone is insufficient because an authenticated malicious user may still attempt an unauthorized transfer.

## Advanced

### Token lifecycle and OAuth flow selection

For interactive public clients, authorization code with PKCE is the normal modern baseline rather than embedding a client secret that cannot remain secret. Validate redirect URIs exactly according to the provider's supported rules and bind the authorization response to the initiating interaction. State, nonce, issuer checks, and PKCE have distinct roles depending on the flow; use a mature library rather than assembling a partial protocol from examples.

Access tokens should have limited audience, privilege, and lifetime. Refresh tokens need stronger protection because they can extend access; use rotation or sender constraints where appropriate and supported. Revocation behavior depends on token style and infrastructure. A self-contained token may remain accepted until expiry unless the service consults an additional revocation mechanism. Logout in one browser is not automatically immediate revocation across every service.

Plan signing-key rotation with overlapping validity, trusted key distribution, cache refresh limits, and failure handling. Do not accept an algorithm solely because a token header requests it. Separate validation rules for different token types to prevent cross-JWT confusion. Clock skew allowances should be bounded and monitored, not used to accept indefinitely expired credentials.

### Injection, XSS, and deserialization

SQL injection is one form of interpreting untrusted data as code. Similar problems occur with shell commands, LDAP filters, template expressions, and unsafe expression evaluators. Prefer structured APIs that separate data from syntax. Escaping rules are context-specific and easy to get wrong when several parsers are involved. Avoid sending untrusted text through a shell merely to run a fixed executable.

Prevent XSS with safe templating, context-aware output encoding, and careful handling of rich HTML. Content Security Policy can reduce impact but is defense in depth, not a repair for unsafe rendering. HTML sanitization and HTML escaping solve different needs: sanitization permits a controlled subset of markup, while escaping displays markup as text.

Do not deserialize arbitrary native Java object streams from untrusted clients. Prefer constrained data formats and explicit schemas, and configure library polymorphism defensively. A JSON document can still trigger unwanted type construction or excessive resource use if the mapper is permissive. Validate depth, size, counts, and allowed fields as well as semantic values.

### SSRF, uploads, and outbound trust

Server-side request forgery occurs when untrusted input directs the server to unintended network destinations. A valid-looking URL is not sufficient validation. Restrict schemes, hosts, ports, redirects, and resolved destinations according to the use case, and enforce network egress controls. Consider DNS changes and private/internal address ranges rather than checking a string once and assuming the eventual connection is safe.

File uploads require size limits, generated storage names, content validation where appropriate, and storage outside executable paths. A filename or content-type header is untrusted. Do not allow path traversal or archive extraction to overwrite arbitrary files. Treat scanners as one layer, and design quarantine and cleanup for interrupted or rejected uploads.

### Tenant and group boundaries across services

Propagate identity and authorization context through trusted mechanisms, not unsigned user-supplied headers. A gateway-authenticated request does not make every internal service exempt from access policy. Services should verify the credential or trusted transport identity and enforce the permissions relevant to their own resources.

Group membership can change while a token remains valid. Decide how sensitive actions respond to stale claims, privilege revocation, and delegated access. For high-impact operations, use current authoritative policy or appropriate step-up authentication rather than assuming a long-lived group claim is sufficient. Record who initiated, approved, and executed an action without leaking credentials into the audit trail.

## Production

### Make secure defaults operable

Deny access unless an explicit policy permits it. Keep secrets outside source control, rotate them, and give each service the minimum database, broker, and network privileges it needs. A configuration mistake should fail safely rather than silently disabling validation. Separate development shortcuts from production configuration and test that they cannot activate accidentally.

Use maintained password-hashing libraries with current adaptive-hash guidance and per-password salts; do not store plaintext or reversible passwords for login verification. Avoid hard-coding work factors in a timeless cheatsheet because hardware and recommendations change. Protect recovery and enrollment flows with the same care as login, including rate limits and resistance to account enumeration.

### Test negative paths and audit safely

Authorization tests should include another user's object, another tenant, missing roles, expired tokens, wrong audience, revoked permissions, and direct calls that bypass the UI. Test denial as a first-class behavior, not only a successful administrator scenario. Property-based or matrix-driven tests help cover combinations of actor, action, resource, and state.

Log authentication and authorization outcomes with safe identifiers and correlation, not raw tokens, passwords, or sensitive bodies. Restrict audit access and retention. Alert on meaningful patterns such as repeated cross-tenant denials or unusual privileged actions, while avoiding unbounded high-cardinality metrics. Security controls that cannot be diagnosed safely often get bypassed during incidents; provide useful controlled diagnostics.

## Exam reasoning

### Match the control to the threat

First name the asset, actor, trust boundary, and failure. Authentication answers identity, authorization answers permission, input validation constrains data, parameterization separates syntax, and output encoding protects a rendering context. None alone replaces the others.

For token questions, distinguish decoding, cryptographic validity, issuer trust, audience, time validity, and permission. For browser questions, inspect how credentials are attached and which origin executes code. CORS is not a substitute for CSRF protection or resource authorization. For multi-tenant questions, trace data through caches, queues, exports, and database queries.

Reject choices that disable validation to solve a configuration mismatch. The correct fix for a wrong audience is a correct token contract, not accepting all audiences. The correct fix for unsafe SQL is structured parameterization and authorization, not merely hiding error messages. Prefer layered controls with explicit ownership and testable denial behavior.

## Cheatsheet

| Concern | Boundary |
| --- | --- |
| Authentication | Who or what is presenting valid credentials |
| Authorization | Which action on which resource in which state |
| Group / role | Identity-store membership / application permission mapping |
| OAuth / OIDC | Delegated authorization / identity layer |
| Access token / ID token | Resource access / client authentication information |
| JWT decode | Reads data; does not establish trust |
| JWT validation | Algorithm, signature, issuer, audience, time, token purpose |
| CSRF | Automatically attached browser credentials |
| CORS | Browser cross-origin response access policy |
| XSS | Untrusted content executing in application origin |
| Injection | Use structured APIs and parameterized values |
| Tenant isolation | Include trusted tenant boundary in every data path |
| SSRF | Restrict actual outbound destinations and redirects |
| Secrets and logs | Least privilege, rotation, redaction, controlled access |

## Check yourself

### 1. Valid login

Can every authenticated user retrieve any invoice by changing its ID?

**Answer:** No. Enforce object-level and tenant authorization independently of login and identifier validity.

### 2. JWT visibility

Does signing a JWT hide its claims?

**Answer:** No. Signing protects integrity and authenticity under a trusted validation contract; it does not inherently encrypt the payload.

### 3. CORS assumption

Does rejecting a cross-origin read through CORS prevent every forged state-changing request?

**Answer:** No. CORS is not a universal request-blocking or CSRF mechanism. Protect cookie-authenticated state changes with appropriate CSRF defenses.

### 4. Advanced: audience mismatch

A valid unexpired token was issued for a different API. Should this API accept it?

**Answer:** No, unless its explicit trusted contract includes this API as an intended audience. Signature validity alone does not establish intended recipient or permission.

### 5. Advanced: cache isolation

Tenant-scoped SQL is correct, but a cache is keyed only by invoice ID. Is isolation complete?

**Answer:** No. The cache can return another tenant's data before SQL runs. Include the authorization-relevant scope and enforce access consistently across the full path.

### 6. Advanced: stale group claim

Does an old administrator group claim always justify a sensitive action after role revocation?

**Answer:** No. Token lifetime and revocation semantics matter. Sensitive operations may require current authoritative policy or a stronger reauthentication/approval boundary.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta Security 3.0; security guidance should be rechecked for the deployed framework and identity provider.

- [Jakarta Security 3.0](https://jakarta.ee/specifications/security/3.0/jakarta-security-spec-3.0)
- [JWT best current practices, RFC 8725](https://www.rfc-editor.org/rfc/rfc8725)
- [OAuth security guidance](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
