# Security Design

## 1. Security Scope

This is a simulated trading platform, but it should still be designed using production-minded security principles.

No real brokerage credentials, bank credentials, financial account information, or real-money order execution should be introduced.

---

## 2. Threat Model

Potential threats include:

- unauthorized simulation control,
- malicious REST requests,
- malformed WebSocket messages,
- oversized messages,
- denial-of-service through repeated connections,
- environment-secret leakage,
- container compromise,
- dependency vulnerabilities,
- log injection,
- unsafe deserialization.

---

## 3. Trust Boundaries

```text
Browser
   |
   | Untrusted
   v
Node Gateway
   |
   | Private network
   v
Analytics
   |
   | Private network
   v
C++ Engine
```

The browser must never be considered trusted.

---

## 4. Authentication

For local development, authentication can be disabled.

For a deployed environment:

- authenticate users,
- use short-lived tokens,
- protect control endpoints,
- validate token claims,
- implement role-based authorization if multiple users exist.

Suggested roles:

```text
VIEWER
OPERATOR
ADMIN
```

---

## 5. Authorization

Example:

| Operation | Viewer | Operator | Admin |
|---|---:|---:|---:|
| View dashboard | Yes | Yes | Yes |
| View metrics | Yes | Yes | Yes |
| Start simulation | No | Yes | Yes |
| Stop simulation | No | Yes | Yes |
| Change config | No | Limited | Yes |
| System administration | No | No | Yes |

---

## 6. Input Validation

Validate:

- JSON structure.
- Numeric ranges.
- String lengths.
- Enum values.
- Order quantities.
- Prices.
- Configuration limits.

Never trust client-side validation alone.

---

## 7. WebSocket Security

Controls should include:

- maximum frame size,
- connection limits,
- authentication,
- origin validation where appropriate,
- heartbeat/ping handling,
- idle timeout,
- graceful disconnect.

The server must not execute arbitrary commands received through WebSocket messages.

---

## 8. REST Security

Use:

- HTTPS in production.
- Authentication for control routes.
- Rate limiting.
- Request size limits.
- Security headers.
- Strict CORS.
- Consistent error responses.

Do not expose stack traces to clients.

---

## 9. Secrets

Secrets belong in environment/secret management.

Never commit:

```text
.env
API keys
JWT signing secrets
private keys
database passwords
```

Commit only:

```text
.env.example
```

with placeholder values.

---

## 10. Container Security

Containers should:

- run as non-root where practical,
- use minimal base images,
- expose only necessary ports,
- avoid privileged mode,
- use read-only filesystems where feasible,
- pin or constrain dependencies,
- receive regular image updates.

---

## 11. Dependency Security

For each language:

### C++

Track third-party libraries.

### Python

Pin or constrain dependencies and review security advisories.

### Node

Use:

```bash
npm audit
```

where appropriate.

### Docker

Regularly rebuild images and scan them using an appropriate container scanner.

---

## 12. Denial-of-Service Controls

A producer can overwhelm the gateway.

Controls:

- rate limits,
- bounded buffers,
- maximum connections,
- maximum message size,
- event aggregation,
- backpressure.

The dashboard should not require one browser update for every engine event.

---

## 13. Logging Security

Do not log:

- secrets,
- access tokens,
- credentials,
- unnecessary personal data.

Sanitize user-controlled values to prevent log injection.

---

## 14. Error Handling

External responses should be safe:

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "invalid simulation speed"
  }
}
```

Internal logs may contain a correlation ID for debugging.

---

## 15. Data Integrity

Trade events are authoritative simulation records.

Consumers should detect:

- duplicate event IDs,
- sequence gaps,
- malformed messages,
- impossible negative quantities,
- invalid timestamps.

Where ordering matters, sequence numbers should be used.

---

## 16. Security Testing

Minimum tests:

- unauthorized start request,
- invalid configuration,
- oversized payload,
- malformed JSON,
- WebSocket connection without required auth,
- rate-limit behavior,
- invalid order quantity,
- invalid price,
- duplicate event handling.

---

## 17. Production Hardening Roadmap

Future additions:

- TLS/mTLS for service-to-service communication.
- OAuth2/OIDC.
- RBAC.
- secret manager.
- network policies.
- signed container images.
- SBOM generation.
- dependency scanning.
- centralized audit logs.
- WAF/reverse proxy.

---

## 18. Security Principle

The project should never confuse "simulation" with "security does not matter."

A portfolio project becomes substantially stronger when it demonstrates that the developer understands where trust ends and validation begins.
