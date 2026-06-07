import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
import warnings
warnings.filterwarnings("ignore")

_BASE_LEGEND = [
    mpatches.Patch(color="#4A90D9", label="Residential"),
    mpatches.Patch(color="#E88B2E", label="Commercial / Retail"),
    mpatches.Patch(color="#9B59B6", label="Industrial"),
    mpatches.Patch(color="#2ECC71", label="Office"),
    mpatches.Patch(color="#E74C3C", label="School"),
    mpatches.Patch(color="#F39C12", label="Church"),
    mpatches.Patch(color="#95A5A6", label="Garage / Service"),
    mpatches.Patch(color="#E8003D", label="Hospital / Medical"),
    mpatches.Patch(color="#BDC3C7", label="Other"),
    plt.Line2D([0], [0], marker="*", color="w", markerfacecolor="#FFC300",
               markersize=12, label="Amenity / Shop"),
    plt.Line2D([0], [0], marker="P", color="w", markerfacecolor="#E8003D",
               markersize=12, label="Medical node"),
]


def plot_base_map(data: dict, ax=None, extra_legend_items=None):
    """
    Draw buildings + amenity nodes + Esri satellite basemap.

    Parameters
    ----------
    data : dict
        Output of osm_loader.load_osm_data().
    ax : matplotlib.axes.Axes, optional
        Existing axes to draw into; creates a new figure if None.
    extra_legend_items : list, optional
        Additional legend handles appended after the base legend.

    Returns
    -------
    fig, ax
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 12))
    else:
        fig = ax.get_figure()

    buildings     = data["buildings"]
    general_nodes = data["general_nodes"]
    medical_nodes = data["medical_nodes"]

    buildings.plot(ax=ax, color=buildings["color"],
                   alpha=0.65, edgecolor="white", linewidth=0.3)

    if not general_nodes.empty:
        general_nodes.plot(ax=ax, color="#FFC300", markersize=28,
                           marker="*", zorder=5, alpha=0.9)

    if not medical_nodes.empty:
        medical_nodes.plot(ax=ax, color="#E8003D", markersize=50,
                           marker="+", linewidths=2.5, zorder=6, alpha=1.0)

    cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery,
                   zoom="auto", alpha=0.85)

    legend_items = _BASE_LEGEND + (extra_legend_items or [])
    ax.legend(handles=legend_items, loc="upper right",
              fontsize=9, framealpha=0.85, title="Building type")

    n_b = len(buildings)
    n_a = len(data["amenities"])
    ax.set_title(
        f"Buildings on the map  ·  {n_b} buildings  +  {n_a} objects",
        fontsize=14, fontweight="bold", pad=12,
    )
    ax.set_axis_off()
    plt.tight_layout()
    return fig, ax
