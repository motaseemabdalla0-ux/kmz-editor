/**
 * KEYMAP geometry-client — the ONLY module allowed to talk to the backend
 * GIS service for the seven Phase 1 operations. Every toolbox call site
 * that needs real geometry math calls a function here, never `fetch()`
 * directly — this is the isolation boundary the architecture plan
 * (docs/plans/KEYMAP_Phase1_Backend_Architecture_Plan.md §2) exists to
 * establish, and it's what makes the eventual toolbox cutover a one-line
 * change per operation instead of a rewrite.
 *
 * NOT WIRED INTO THE APP YET. Per this phase's explicit instruction ("keep
 * frontend unchanged"), the existing toolbox functions in the shipped
 * kmz_editor (2).html / index.html still use their original local math.
 * This file is the complete, tested client for the next phase's cutover —
 * see the migration plan's Stage 3/4 for what "wiring it in" means.
 *
 * Every function here:
 *   1. Calls the backend.
 *   2. On success, returns { ok: true, data, source: "backend" }.
 *   3. On failure (network error, timeout, non-2xx, backend down) —
 *      logs a console.warn (the "graceful fallback with warning logs"
 *      requirement) and returns { ok: false, error, source: "backend" },
 *      WITHOUT throwing. The caller decides what "graceful" means for that
 *      specific tool (e.g. fall back to the existing local approximate
 *      math and tell the user, per the architecture plan §6.6).
 *
 * This module intentionally has NO fallback math of its own — that math
 * already exists in the shipped app's geo.js and should stay exactly where
 * it is; duplicating it here would be a second copy to keep in sync.
 */

const DEFAULT_BASE_URL = "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 8000;

/**
 * @param {object} [opts]
 * @param {string} [opts.baseUrl] - defaults to the local Docker service.
 * @param {number} [opts.timeoutMs]
 */
function createGeometryClient(opts = {}) {
  const baseUrl = (opts.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const timeoutMs = opts.timeoutMs || DEFAULT_TIMEOUT_MS;

  async function post(path, body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(baseUrl + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      const payload = await res.json().catch(() => null);
      if (!res.ok) {
        const errShape = payload && payload.error ? payload.error : { code: "http_error", message: res.statusText };
        console.warn(
          `[geometry-client] ${path} failed (${res.status} ${errShape.code}): ${errShape.message} — ` +
          "falling back to local calculation."
        );
        return { ok: false, error: errShape, source: "backend" };
      }
      return { ok: true, data: payload, source: "backend" };
    } catch (err) {
      const reason = err && err.name === "AbortError" ? "timeout" : (err && err.message) || String(err);
      console.warn(
        `[geometry-client] ${path} unreachable (${reason}) — backend may be down; ` +
        "falling back to local calculation."
      );
      return { ok: false, error: { code: "unreachable", message: reason }, source: "backend" };
    } finally {
      clearTimeout(timer);
    }
  }

  async function health() {
    try {
      const res = await fetch(baseUrl + "/v1/health", { method: "GET" });
      if (!res.ok) return false;
      const body = await res.json().catch(() => null);
      return !!body && body.status === "ok";
    } catch (err) {
      console.warn(`[geometry-client] health check failed: ${(err && err.message) || err}`);
      return false;
    }
  }

  return {
    baseUrl,
    health,

    /** Buffer N features by distance_m. Replaces buildBuffer()'s radial-offset approximation once wired in. */
    buffer(features, distanceM, { capStyle = "round", joinStyle = "round", crs = "EPSG:4326" } = {}) {
      return post("/v1/geometry/buffer", {
        features, distance_m: distanceM, cap_style: capStyle, join_style: joinStyle, crs,
      });
    },

    /** Full polygon-polygon join. Replaces spatialJoin()'s centroid-in-polygon test once wired in. */
    spatialJoin(sourceFeatures, targetFeatures, field, predicate = "intersects") {
      return post("/v1/geometry/spatial-join", {
        source_features: sourceFeatures, target_features: targetFeatures, field, predicate,
      });
    },

    /** Net-new: no prior implementation existed on the frontend. */
    intersection(featuresA, featuresB, { minAreaM2 } = {}) {
      return post("/v1/geometry/intersection", {
        features_a: featuresA, features_b: featuresB,
        min_area_m2: minAreaM2 === undefined ? null : minAreaM2,
      });
    },

    /** Net-new: no toolbox button calls this yet — see the architecture plan §3.5. */
    union(features) {
      return post("/v1/geometry/union", { features });
    },

    /** Replaces the spherical-excess area approximation used for the KPI strip / stats panel. */
    area(features, crs = "EPSG:4326") {
      return post("/v1/geometry/area", { features, crs });
    },

    /**
     * Bulk/programmatic distance only — NOT the live drag-to-measure map
     * HUD, which stays on local haversine math by design (design doc §3.7).
     */
    distance(geometryA, geometryB, crs = "EPSG:4326") {
      return post("/v1/geometry/distance", { geometry_a: geometryA, geometry_b: geometryB, crs });
    },

    /** Built ahead of its UI trigger — enables SHP import in a later phase without a backend change. */
    reproject(features, sourceCrs, targetCrs = "EPSG:4326") {
      return post("/v1/geometry/reproject", { features, source_crs: sourceCrs, target_crs: targetCrs });
    },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createGeometryClient };
}
