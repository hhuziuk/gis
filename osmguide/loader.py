import osmium
import geopandas as gpd
from shapely.geometry import Point, Polygon
import warnings
warnings.filterwarnings("ignore")

WGS84 = "EPSG:4326"
WEB   = "EPSG:3857"

MEDICAL_AMENITIES = frozenset({
    "hospital", "clinic", "doctors", "pharmacy",
    "dentist", "nursing_home", "health_post",
})

BUILDING_COLORS = {
    "residential": "#4A90D9",
    "apartments":  "#4A90D9",
    "house":       "#6CB4E4",
    "commercial":  "#E88B2E",
    "retail":      "#E88B2E",
    "industrial":  "#9B59B6",
    "office":      "#2ECC71",
    "school":      "#E74C3C",
    "church":      "#F39C12",
    "garage":      "#95A5A6",
    "service":     "#95A5A6",
    "hospital":    "#E8003D",
    "healthcare":  "#E8003D",
}


def is_medical(amenity, healthcare) -> bool:
    """String-safe check — never truthy on NaN."""
    return (isinstance(amenity, str) and amenity in MEDICAL_AMENITIES) or \
           (isinstance(healthcare, str) and bool(healthcare))


class _NodeLocationHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.locations: dict[int, tuple[float, float]] = {}

    def node(self, n):
        if n.location.valid():
            self.locations[n.id] = (n.location.lon, n.location.lat)


class _BuildingHandler(osmium.SimpleHandler):
    def __init__(self, node_locs):
        super().__init__()
        self._locs = node_locs
        self.building_polys: list[dict] = []
        self.amenity_points: list[dict] = []

    def node(self, n):
        tags = dict(n.tags)
        if any(k in tags for k in ("amenity", "shop", "office", "leisure", "healthcare")):
            if n.location.valid():
                self.amenity_points.append(
                    {"geometry": Point(n.location.lon, n.location.lat), **tags}
                )

    def way(self, w):
        tags = dict(w.tags)
        amenity    = tags.get("amenity", "")
        healthcare = tags.get("healthcare", "")
        med = is_medical(amenity, healthcare)

        if "building" not in tags and not med:
            return
        if "building" not in tags:
            tags["building"] = amenity or healthcare or "hospital"

        coords = [self._locs[r.ref] for r in w.nodes if r.ref in self._locs]
        if len(coords) < 3:
            return
        try:
            poly = Polygon(coords)
            if poly.is_valid and not poly.is_empty:
                self.building_polys.append({"geometry": poly, **tags})
        except Exception:
            pass


def load_osm_data(pbf_path: str) -> dict:
    """
    Parse a .pbf file and return a dict of GeoDataFrames (all EPSG:3857):
      data["buildings"]      — building polygons with a "color" column
      data["amenities"]      — all amenity/shop/office nodes
      data["medical_nodes"]  — medical subset of amenities
      data["general_nodes"]  — non-medical subset of amenities
    """
    loc_handler = _NodeLocationHandler()
    loc_handler.apply_file(pbf_path)

    bld_handler = _BuildingHandler(loc_handler.locations)
    bld_handler.apply_file(pbf_path)

    gdf_buildings = gpd.GeoDataFrame(bld_handler.building_polys, crs=WGS84).to_crs(WEB)
    gdf_amenities = gpd.GeoDataFrame(bld_handler.amenity_points, crs=WGS84).to_crs(WEB)

    gdf_buildings["color"] = gdf_buildings.apply(
        lambda r: "#E8003D" if is_medical(r.get("amenity"), r.get("healthcare"))
                  else BUILDING_COLORS.get(r.get("building", ""), "#BDC3C7"),
        axis=1,
    )

    mask = gdf_amenities.apply(
        lambda r: is_medical(r.get("amenity"), r.get("healthcare")), axis=1
    )

    return {
        "buildings":     gdf_buildings,
        "amenities":     gdf_amenities,
        "medical_nodes": gdf_amenities[mask].reset_index(drop=True),
        "general_nodes": gdf_amenities[~mask].reset_index(drop=True),
    }
