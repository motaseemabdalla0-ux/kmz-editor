# KEYMAP GIS Service — Architecture Decisions

This documents *why* the code is built the way it is, for anyone picking this
up later. It complements, and does not repeat, the approved design document
at `../docs/plans/KEYMAP_Phase1_Backend_Architecture_Plan.md` — read that
first for the API contracts and the Phase 1 scope boundary. This file covers
decisions made or refined *during implementation*, several of which turned
out differently than the design doc predicted, and says so explicitly.

## 1. Statelessness is real, not aspirational

No database, no ORM, no migrations, no persisted request history. Every
endpoint is a pure function of its request body. This was the design intent
and it held exactly as planned — there was no point during implementation
where statelessness needed to bend.

## 2. GDAL is not a Phase 1 runtime dependency (a correction to the design doc)

The design document flagged GDAL packaging as a real deployment risk and
recommended `pyogrio` over `fiona` to mitigate it. During implementation it
became clear the mitigation wasn't needed *yet*: GeoPandas' core operations
used in this phase — `GeoDataFrame` construction, `sjoin`, `overlay`,
`.area`, `.distance`, `.to_crs` — depend only on `shapely` + `pyproj` +
`pandas`. GDAL is only invoked by `geopandas.read_file()` /
`.to_file()` (file format I/O), and **Phase 1 has zero file-upload
endpoints** — every request carries GeoJSON geometry in a JSON body, never a
file. `requirements.txt` does not list `pyogrio`/`fiona`/GDAL at all.

One caveat found during the actual Docker build: GeoPandas 1.1.x pulls in
`pyogrio` **transitively** as a dependency of its own, even though this
service never calls the functions that need it. This did not reintroduce
the packaging risk — `pyogrio`'s wheel bundles a self-contained GDAL binary,
so no `apt-get install gdal-bin` was needed and the build completed in
~77 seconds. The Dockerfile stayed a plain `python:3.12-slim` image with no
GDAL system package, exactly as hoped, just via a slightly different path
than predicted.

**This changes the moment a later phase adds Shapefile import** (real file
I/O, needing an actual read engine) — re-evaluate `pyogrio` vs `fiona`
properly at that point rather than assuming today's finding still holds.

## 3. The GeoJSON <-> Shapely boundary is one module, on purpose

`app/core/geometry_io.py` is the only place a raw dict becomes a Shapely
geometry or vice versa. This exists because the architecture plan correctly
identified the real risk in this project as the *glue code*, not Shapely
itself (§7 of the design doc) — id-preservation across a batch, malformed
input, self-touching rings from hand-digitized KML exports. Concretely,
`parse_geometry()` attempts a zero-width-buffer repair (`geom.buffer(0)`) on
an invalid-but-parseable geometry before rejecting it — a standard, safe
fix for the most common real-world defect (a ring that touches itself at
one point) rather than failing on data that every other GIS tool in the
chain (QGIS, ArcGIS) would silently accept.

## 4. Metric operations always run in a projected CRS, never in degrees

Buffer distance, area, and distance are all meaningless computed directly
on WGS84 (an angular CRS) — this was the root defect motivating this whole
phase. `app/core/crs_utils.py` reprojects to a metric CRS before any of
these three operations, either the caller's explicit `target_crs` or an
auto-selected UTM zone from the geometry's centroid (`utm_epsg_for_lonlat`,
the standard `floor((lon+180)/6)+1` formula — general-purpose, not
hardcoded to Saudi Arabia's zones, verified in `test_crs.py` against
AlUla's actual zone, EPSG:32637).

For **batch** area requests (`/geometry/area` over N features), one shared
UTM zone is chosen from the whole batch's combined centroid rather than a
per-feature zone. This is correct and efficient for KEYMAP's real usage
pattern — one merged dataset covering a single region (AlUla, in every
verification run so far) — and would need revisiting only if a future
dataset spanned multiple UTM zones widely enough for the shared-zone
approximation to matter.

## 5. `geopandas.sjoin` (R-tree indexed) instead of a manual loop

`join_service.py` uses GeoPandas' spatial-index-backed `sjoin` rather than
a nested `for` loop testing every target against every source. This isn't
just cleaner code — it's the direct scalability fix the frontend's O(n·m)
overlap/join logic didn't have, relevant at the ~2,785-plot dataset size
this project has actually tested against.

## 6. A real bug this caught: pandas' `NaN` is not Python's `None`

Worth recording because it's the kind of mistake that's easy to reintroduce.
`gpd.sjoin(..., how="left")` fills unmatched rows with `NaN`, not `None` —
the first implementation checked `row.get("source_id") is not None`, which
is `True` for a `NaN` float, so every unmatched target was incorrectly
counted as matched. `test_join_no_overlap_is_unmatched` caught this
immediately; the fix is `pd.notna(...)`. This is exactly the "conversion
and integration code" risk class the design doc's §7 predicted, and it's
also exactly why that fixture-based test suite exists rather than trusting
Shapely/GeoPandas' correctness to imply the service layer is bug-free too.

## 7. Errors are one shape, everywhere

`{"error": {"code", "message", "detail"}}` — a `GeometryError` exception
type that services raise and a single FastAPI exception handler in
`main.py` translates, plus a catch-all handler for anything unexpected
(logged with the request path, never the payload — see SECURITY.md). No
endpoint hand-rolls its own error response.

## 8. `/v1/` from day one

Every route is under `/v1/geometry/...`. A breaking response-shape change
in a later phase ships as `/v2/`, giving the frontend adapter time to
migrate rather than breaking on a silent deploy.

## 9. Two endpoints exist with no UI trigger yet — by instruction, not oversight

`/geometry/union` and `/geometry/reproject` are fully implemented and
tested, but no toolbox button calls them (see `geometry-client.js`'s header
comment). This was explicit scope in the approved design doc (§3.5, §3.8):
build the contract now, wire the UI in a later phase. Listed here so it
isn't mistaken for incomplete work.
