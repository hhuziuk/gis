import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pyproj
import s2sphere as s2
from shapely.geometry import Polygon
from osmguide import load_osm_data, SAMPLE_PBF, plot_base_map

data = load_osm_data(SAMPLE_PBF)
buildings = data["buildings"]

to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
to_web   = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

bounds = buildings.total_bounds  # (minx, miny, maxx, maxy) in EPSG:3857
lon_min, lat_min = to_wgs84.transform(bounds[0], bounds[1])
lon_max, lat_max = to_wgs84.transform(bounds[2], bounds[3])

region = s2.LatLngRect(
    s2.LatLng.from_degrees(lat_min, lon_min),
    s2.LatLng.from_degrees(lat_max, lon_max),
)

COARSE_LEVEL = 13   # ~1 km²  per cell at this latitude
FINE_LEVEL   = 15   # ~60 000 m² per cell


def _cover(region, level):
    rc = s2.RegionCoverer()
    rc.min_level = level
    rc.max_level = level
    rc.max_cells = 2000
    return rc.get_covering(region)


def _cell_to_poly(cell_id):
    """Return a Shapely Polygon (EPSG:3857) for one S2 cell."""
    cell = s2.Cell(cell_id)
    pts = []
    for k in range(4):
        ll = s2.LatLng.from_point(cell.get_vertex(k))
        x, y = to_web.transform(ll.lng().degrees, ll.lat().degrees)
        pts.append((x, y))
    return Polygon(pts)


coarse_ids   = _cover(region, COARSE_LEVEL)
fine_ids     = _cover(region, FINE_LEVEL)
coarse_polys = [_cell_to_poly(c) for c in coarse_ids]
fine_polys   = [_cell_to_poly(c) for c in fine_ids]

# --- Plot 1: coarse cells (level 13) with token labels ---
fig1, ax1 = plot_base_map(data)

for poly, cid in zip(coarse_polys, coarse_ids):
    x, y = poly.exterior.xy
    ax1.fill(x, y, alpha=0.18, color="#FFE000", zorder=4)
    ax1.plot(x, y, color="#FFE000", linewidth=2.5, alpha=0.95, zorder=5)
    cx, cy = poly.centroid.x, poly.centroid.y
    ax1.text(cx, cy, cid.to_token(), ha="center", va="center",
             fontsize=7, color="white", fontweight="bold", zorder=6,
             bbox=dict(boxstyle="round,pad=0.15", facecolor="black",
                       alpha=0.55, linewidth=0))

ax1.add_patch(mpatches.Rectangle(
    (0, 0), 0, 0, facecolor="#FFE000", alpha=0.6,
    label=f"Level {COARSE_LEVEL} — {len(coarse_polys)} cells (~1 km² each)",
))
ax1.legend(loc="upper left", fontsize=9, framealpha=0.85)
ax1.set_title(
    f"S2 — level {COARSE_LEVEL} (coarse grid, {len(coarse_polys)} cells)",
    fontsize=13, fontweight="bold", pad=10,
)
plt.show()

# --- Plot 2: fine cells (level 15) ---
fig2, ax2 = plot_base_map(data)

for poly in fine_polys:
    x, y = poly.exterior.xy
    ax2.fill(x, y, alpha=0.09, color="#00FF80", zorder=4)
    ax2.plot(x, y, color="#00FF80", linewidth=0.7, alpha=0.8, zorder=5)

ax2.add_patch(mpatches.Rectangle(
    (0, 0), 0, 0, facecolor="#00FF80", alpha=0.5,
    label=f"Level {FINE_LEVEL} — {len(fine_polys)} cells (~60 000 m² each)",
))
ax2.legend(loc="upper left", fontsize=9, framealpha=0.85)
ax2.set_title(
    f"S2 — level {FINE_LEVEL} (fine grid, {len(fine_polys)} cells)",
    fontsize=13, fontweight="bold", pad=10,
)
plt.show()

# --- Plot 3: both levels overlaid ---
fig3, ax3 = plot_base_map(data)

for poly in fine_polys:
    x, y = poly.exterior.xy
    ax3.fill(x, y, alpha=0.08, color="#00FF80", zorder=4)
    ax3.plot(x, y, color="#00FF80", linewidth=0.6, alpha=0.7, zorder=4)

for poly in coarse_polys:
    x, y = poly.exterior.xy
    ax3.plot(x, y, color="#FFE000", linewidth=2.5, alpha=0.95, zorder=5)

ax3.add_patch(mpatches.Rectangle(
    (0, 0), 0, 0, edgecolor="#FFE000", facecolor="none", linewidth=2,
    label=f"Level {COARSE_LEVEL} — {len(coarse_polys)} cells (coarse)",
))
ax3.add_patch(mpatches.Rectangle(
    (0, 0), 0, 0, facecolor="#00FF80", alpha=0.5,
    label=f"Level {FINE_LEVEL} — {len(fine_polys)} cells (fine)",
))
ax3.legend(loc="upper left", fontsize=9, framealpha=0.85)
ax3.set_title(
    f"S2 Cell Index — levels {COARSE_LEVEL} and {FINE_LEVEL} overlaid",
    fontsize=13, fontweight="bold", pad=10,
)
plt.show()
