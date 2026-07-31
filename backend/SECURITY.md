# KEYMAP GIS Service — Security Considerations (Phase 1)

**Read this before deploying anywhere other than local Docker.** This
service ships in Phase 1 with **no authentication, by explicit instruction**
("no PostGIS, no authentication, no other enterprise features yet"). That's
a legitimate scope decision for a local development milestone; it is not a
posture this document is claiming is safe for real-world exposure. This
file exists to say precisely where the line is.

## What's implemented as a compensating control

None of these are substitutes for authentication. They're what keeps a
*local, trusted-network* deployment reasonable in the meantime.

| Control | Where | What it does |
|---|---|---|
| CORS origin allowlist | `app/core/config.py` `cors_origins`, enforced in `main.py` | Never a wildcard. Verified live: an allowed origin gets `access-control-allow-origin`; an unknown origin gets no CORS header at all — a browser blocks the response client-side. Confirmed with real `curl -H "Origin: ..."` requests against the running container, not just unit tests. |
| Request body size limit | `BodySizeLimitMiddleware` in `main.py`, default 15 MB | Rejects an oversized request with a clean `413` before it reaches a handler, rather than letting an unbounded GeoJSON payload degrade the process. Verified live against the running container. |
| No payload logging | `app/core/logging.py` | Structured logs record operation name, feature counts, and duration — never geometry or attribute *contents*. Verified: the container's logs after a full smoke-test session contain zero coordinate data. |
| Structured error responses | `app/core/errors.py` + exception handlers | No stack traces or internal detail leak to the client on an unhandled error — `unhandled_error_handler` returns a fixed generic message and logs the real exception server-side only. |

## What's explicitly NOT implemented, and must land before this is anything other than local/trusted-network

- **Authentication / authorization.** The API is reachable by anyone who
  can reach the host. On `localhost`, that's the developer. The moment
  this is deployed anywhere reachable over a network you don't fully
  control, this is the first gap to close — not a nice-to-have.
- **Rate limiting.** No `slowapi` or equivalent is wired in. Documented as
  a recommendation in the architecture plan; not implemented this phase,
  because it wasn't in the explicit Phase 1 instruction and CORS + body
  limits are the agreed-sufficient guardrail for a local Docker deployment.
- **TLS.** `uvicorn` serves plain HTTP inside the container in this local
  setup. A real deployment needs TLS termination (a reverse proxy or the
  platform's managed HTTPS) — relevant the moment the frontend (served over
  HTTPS on GitHub Pages) needs to call this service from anywhere but
  `localhost`, since browsers block HTTPS→HTTP mixed content.
- **Secrets management.** There are none yet — no API keys, no database
  credentials, nothing to leak. Worth stating so it's clear this isn't an
  oversight, just genuinely not applicable to a stateless, credential-free
  service yet.

## The data-minimization decision, made concrete

The architecture plan flagged, at the design stage, that this backend
reverses KEYMAP's one property explicitly named a strength in the Phase 0
report: **zero data ever left the browser, until now.** That trade-off is
real and this implementation does not try to hide it — but two concrete
choices limit its blast radius:

1. **No persistence.** A request's geometry exists in server memory for the
   duration of that one request and is gone. There is no database row, no
   log line, no file on disk containing it afterward — verified above by
   inspecting the actual container logs.
2. **Geometry only, where the operation allows it.** `/geometry/spatial-join`
   is the one endpoint that necessarily carries attribute values (the field
   being copied) — every other endpoint needs geometry alone.

**This does not replace a governance decision RCU has not yet made.** If
plot/land-use geometry is classified as sensitive, sending it to any
hosted service — even one you control, even with these mitigations —
needs sign-off before this goes past `localhost`. That was true when the
architecture plan raised it and remains true now that the code exists.

## Threat model, Phase 1 (local Docker only)

| Actor | Can they reach this service? | Consequence if they do |
|---|---|---|
| The developer, on `localhost` | Yes, by design | None — this is the intended user this phase |
| Anything else on the local network | Only if the container is bound to `0.0.0.0` and the network is untrusted | Could call any of the 7 endpoints with no auth — mitigate by keeping Docker's port binding to `127.0.0.1` outside of active local development, or a firewalled dev network |
| The public internet | Not reachable — nothing in this phase deploys it beyond local Docker | N/A this phase; becomes the primary threat model the moment any cloud deployment happens, which is why auth is the first item in any phase that does that |

## Before any deployment beyond local Docker

1. Authentication (even a simple API key/bearer token is a large
   improvement over nothing).
2. Rate limiting.
3. TLS (via the hosting platform's managed HTTPS or a reverse proxy).
4. RCU data-governance sign-off on plot/land-use geometry leaving the
   browser (see above — an organizational decision, not an engineering
   task).
5. Re-evaluate CORS origins for the actual deployed frontend URL(s).

None of these are Phase 1 scope. All of them are the explicit next gate
before this stops being a local development service.
