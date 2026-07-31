"""
Real polygon-polygon spatial join, replacing the frontend's centroid-in-
polygon test — which misses any target whose *centroid* falls outside an
enclosing source polygon even though the shapes genuinely overlap (Phase 0
report §2.3).

Uses GeoPandas' sjoin, which is spatial-index-backed (R-tree) rather than
the frontend's O(n*m) brute-force loop — this is also a real scalability
improvement at the ~2,785-plot dataset size this project has tested against.
"""
from typing import List

import geopandas as gpd
import pandas as pd

from app.core.geometry_io import features_to_gdf
from app.core.logging import logger
from app.models.common import Feature


def spatial_join(source_features: List[Feature], target_features: List[Feature], field: str, predicate: str):
    source_gdf = features_to_gdf([f.model_dump() for f in source_features])
    target_gdf = features_to_gdf([f.model_dump() for f in target_features])

    source_gdf = source_gdf.rename(columns={"id": "source_id"})
    target_gdf = target_gdf.rename(columns={"id": "target_id"})[["target_id", "geometry"]]

    if field not in source_gdf.columns:
        return {"matches": [], "matched_count": 0, "target_count": len(target_gdf),
                "unmatched_target_ids": target_gdf["target_id"].tolist()}

    joined = gpd.sjoin(target_gdf, source_gdf[["source_id", field, "geometry"]], predicate=predicate, how="left")

    # A target overlapping more than one source is a real, expected case
    # (e.g. two adjacent zoning layers) — keep the first match by source
    # order and log it rather than silently picking one with no record.
    dupes = joined[joined.duplicated("target_id", keep=False)]
    if not dupes.empty:
        logger.warning("spatial_join: %d target feature(s) matched more than one source; keeping first",
                        dupes["target_id"].nunique())
    joined = joined.drop_duplicates("target_id", keep="first")

    # A "left" join leaves NaN (not None/null) in source_id/field for a
    # target with no match — pandas' missing-value sentinel for object
    # columns is float('nan'), which `is not None` does NOT catch. This was
    # caught by test_join_no_overlap_is_unmatched during Phase 1 verification.
    matches = []
    matched_ids = set()
    for _, row in joined.iterrows():
        if pd.notna(row.get("source_id")) and pd.notna(row.get(field)):
            matches.append({"target_id": row["target_id"], "source_id": row["source_id"], "value": row[field]})
            matched_ids.add(row["target_id"])

    all_target_ids = target_gdf["target_id"].tolist()
    unmatched = [t for t in all_target_ids if t not in matched_ids]

    return {
        "matches": matches,
        "matched_count": len(matches),
        "target_count": len(all_target_ids),
        "unmatched_target_ids": unmatched,
    }
