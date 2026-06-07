import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from rtree import index as rtree_index
from shapely.geometry import box
from osmguide import load_osm_data, SAMPLE_PBF, plot_base_map

data = load_osm_data(SAMPLE_PBF)
buildings = data["buildings"]
geoms = list(buildings.geometry)

NODE_CAPACITY = 16

# Build spatial index via bulk loading; rtree uses STR sorting internally.
p = rtree_index.Property()
p.leaf_capacity = NODE_CAPACITY
idx = rtree_index.Index(
    ((i, g.bounds, None) for i, g in enumerate(geoms)),
    properties=p,
)

# Leaf nodes from the actual rtree structure: (node_id, [item_ids], [minx, miny, maxx, maxy])
leaves = idx.leaves()
leaf_mbrs = [box(*lf[2]) for lf in leaves]
leaf_nodes_with_idx = [(box(*lf[2]), lf[1]) for lf in leaves]

# Mid-level MBRs: rtree does not expose internal nodes, so STR-group the leaf MBRs
# to approximate the level-1 bounding boxes the tree uses internally.
def _str_group(mbrs, capacity):
    centroids = np.array([(m.centroid.x, m.centroid.y) for m in mbrs])
    S = max(1, int(np.ceil(np.sqrt(len(mbrs) / capacity))))
    x_order = np.argsort(centroids[:, 0])
    ss = int(np.ceil(len(mbrs) / S))
    groups = []
    for s in range(S):
        strip = x_order[s * ss:(s + 1) * ss]
        y_order = strip[np.argsort(centroids[strip, 1])]
        for j in range(0, len(y_order), capacity):
            bucket = y_order[j:j + capacity]
            gs = [mbrs[k] for k in bucket]
            groups.append(box(
                min(g.bounds[0] for g in gs), min(g.bounds[1] for g in gs),
                max(g.bounds[2] for g in gs), max(g.bounds[3] for g in gs),
            ))
    return groups

mid_nodes = _str_group(leaf_mbrs, NODE_CAPACITY)
root_bounds = idx.bounds  # (minx, miny, maxx, maxy)

# --- Plot 1: MBR hierarchy ---
fig1, ax = plot_base_map(data)

rx, ry = root_bounds[0], root_bounds[1]
rw, rh = root_bounds[2] - rx, root_bounds[3] - ry
ax.add_patch(mpatches.Rectangle((rx, ry), rw, rh,
    linewidth=3, edgecolor="#00CFFF", facecolor="none", zorder=6,
    label=f"Level 0 — root (1 node)"))

for mbr in mid_nodes:
    b = mbr.bounds
    ax.add_patch(mpatches.Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1],
        linewidth=2, edgecolor="#FFE000", facecolor="#FFE000", alpha=0.12, zorder=5))
ax.add_patch(mpatches.Rectangle((0,0),0,0,
    linewidth=2, edgecolor="#FFE000", facecolor="none",
    label=f"Level 1 — {len(mid_nodes)} nodes"))

for mbr in leaf_mbrs:
    b = mbr.bounds
    ax.add_patch(mpatches.Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1],
        linewidth=0.8, edgecolor="#00FF80", facecolor="none", alpha=0.7, zorder=4))
ax.add_patch(mpatches.Rectangle((0,0),0,0,
    linewidth=0.8, edgecolor="#00FF80", facecolor="none",
    label=f"Level 2 — {len(leaf_mbrs)} leaf nodes"))

ax.legend(loc="upper left", fontsize=9, framealpha=0.85)
ax.set_title("R-Tree — MBR hierarchy on 1 344 building footprints",
             fontsize=13, fontweight="bold", pad=10)
plt.show()

# --- Plot 2: range query + pruning ---
cx = (root_bounds[0] + root_bounds[2]) / 2
cy = (root_bounds[1] + root_bounds[3]) / 2
qw = (root_bounds[2] - root_bounds[0]) * 0.25
qh = (root_bounds[3] - root_bounds[1]) * 0.25
query = box(cx - qw/2, cy - qh/2, cx + qw/2, cy + qh/2)

hit_leaves  = [m for m in leaf_mbrs if m.intersects(query)]
miss_leaves = [m for m in leaf_mbrs if not m.intersects(query)]
hit_mid     = [m for m in mid_nodes if m.intersects(query)]

# idx.intersection returns candidates whose bounding boxes overlap the query;
# the geometry check below filters out false positives.
candidate_ids = list(idx.intersection(query.bounds))
result_idx = [i for i in candidate_ids if geoms[i].intersects(query)]

fig2, ax = plot_base_map(data)
qb = query.bounds

for mbr in miss_leaves:
    b = mbr.bounds
    ax.add_patch(mpatches.Rectangle((b[0],b[1]), b[2]-b[0], b[3]-b[1],
        linewidth=1.5, edgecolor="#FF4444", facecolor="#FF4444", alpha=0.35, zorder=3))

for mbr in hit_leaves:
    b = mbr.bounds
    ax.add_patch(mpatches.Rectangle((b[0],b[1]), b[2]-b[0], b[3]-b[1],
        linewidth=2, edgecolor="#FF8000", facecolor="#FF8000", alpha=0.25, zorder=4))

for mbr in hit_mid:
    b = mbr.bounds
    ax.add_patch(mpatches.Rectangle((b[0],b[1]), b[2]-b[0], b[3]-b[1],
        linewidth=2.5, edgecolor="#FFE000", facecolor="none", zorder=5))

ax.add_patch(mpatches.Rectangle((qb[0],qb[1]), qb[2]-qb[0], qb[3]-qb[1],
    linewidth=3, edgecolor="#FF1493", facecolor="#FF1493", alpha=0.15, zorder=6,
    label="Query box"))

if result_idx:
    buildings.iloc[result_idx].plot(ax=ax, color="#00FFFF", alpha=0.9, zorder=7)

pruned, visited = len(miss_leaves), len(hit_leaves)
ax.add_patch(mpatches.Rectangle((0,0),0,0,
    linewidth=1.5, edgecolor="#FF4444", facecolor="#FF4444", alpha=0.35,
    label=f"Pruned subtrees ({pruned})"))
ax.add_patch(mpatches.Rectangle((0,0),0,0,
    linewidth=2, edgecolor="#FF8000", facecolor="none",
    label=f"Visited subtrees ({visited})"))
ax.add_patch(mpatches.Rectangle((0,0),0,0,
    color="#00FFFF", label=f"Result buildings ({len(result_idx)})"))

ax.legend(loc="upper left", fontsize=9, framealpha=0.85)
ax.set_title(
    f"R-Tree range query — {pruned}/{pruned+visited} subtrees pruned "
    f"({100*pruned/(pruned+visited):.0f}% work saved)",
    fontsize=12, fontweight="bold", pad=10)
plt.show()
