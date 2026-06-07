"""osmguide — data-preparation helpers for the GIS learning guide.

The package turns raw OpenStreetMap data into analysis-ready GeoDataFrames and
provides the one shared satellite base-map renderer that every lesson draws on.
Index computations themselves live in the lesson notebooks under ``topics/``.

Typical use from any notebook, regardless of folder depth::

    from osmguide import load_osm_data, SAMPLE_PBF
    data = load_osm_data(SAMPLE_PBF)
"""

from pathlib import Path

from .loader import load_osm_data
from .base_map import plot_base_map

# Absolute path to the bundled sample dataset, resolved relative to this file so
# the one-line load works from any working directory (assumes an editable install).
SAMPLE_PBF = str(Path(__file__).resolve().parents[1] / "datasets" / "my_area.osm.pbf")

__all__ = ["load_osm_data", "plot_base_map", "SAMPLE_PBF"]
