# frontend/

`geometry-client.js` is the HTTP adapter for the KEYMAP GIS backend
(`../backend/`) — see its header comment for the full explanation.

**Status: not wired into the shipped app.** `index.html` / `keymap_cdn.html`
at the repo root are unchanged this phase, per the explicit Phase 1
instruction to keep the frontend as-is. This file exists as a complete,
tested client ready for the next phase's toolbox cutover (see the
architecture plan's migration stages 3–4).

Verified against the live local backend during implementation: successful
calls (buffer/area/union), a backend-rejected malformed geometry (returns
`{ok: false, error}`, does not throw), and an unreachable backend (returns
`{ok: false}`, logs a `console.warn`, does not throw) — all three paths
behave as designed.
