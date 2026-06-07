# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **hands-on learning guide for GIS / OpenStreetMap analysis**. It is organized as a
set of self-contained topic folders. Each topic teaches one concept (e.g. an
accessibility index, a density index) and ships in two parallel forms:

| file | purpose |
|---|---|
| `README.md` | the theory — prose, formulas, and **static images** of the expected result |
| `<topic>.ipynb` | the same lesson, but the images are replaced by **runnable code** that reproduces them live |

The two files must stay in sync: the notebook is the executable proof of what the
markdown describes. A reader can browse the `README.md` for understanding, or open the
notebook and run it to reproduce every figure.

```
gis/
├── pyproject.toml            # editable install: `pip install -e ".[notebooks]"`
├── datasets/                 # small, committed sample data (the single source of truth)
│   └── my_area.osm.pbf
├── osmguide/                 # the installable helper package — data prep + shared rendering
│   ├── __init__.py           #   public API + SAMPLE_PBF
│   ├── __main__.py           #   `python -m osmguide` smoke-test demo
│   ├── loader.py             #   data layer (pbf → ready GeoDataFrames)
│   └── base_map.py           #   the one shared satellite base-map renderer
└── topics/
    └── <topic>/              # one folder per lesson
        ├── README.md         #   theory + result images
        └── <topic>.ipynb     #   theory + runnable code (this is where indices are computed)
```

The helper package is **purely data preparation + shared rendering**. Index computations and
their visualizations are **lesson content**, authored in the `topics/<topic>/` notebooks — not
in the package.

## The data-loading contract (most important constraint)

A learner must be able to load any dataset and start working in **no more than three
lines**, and ideally one call. The `osmguide` package exists to make this true. The
canonical opening of every notebook is:

```python
from osmguide import load_osm_data, SAMPLE_PBF
data = load_osm_data(SAMPLE_PBF)   # → dict of GeoDataFrames, ready to plot
```

`SAMPLE_PBF` is an absolute path resolved inside the package, so the load works from any
folder depth without `sys.path` hacks (the package is installed editable).

When adding a new dataset or loader, preserve this property:
- expose **one** public entry point that returns analysis-ready objects (GeoDataFrames in
  a fixed CRS), never raw handles the caller must post-process;
- do all parsing, cleaning, and CRS conversion **inside** the loader;
- keep heavy/parsing logic out of the notebooks — notebooks call the library, they do not
  reimplement it.

## Engineering principles (apply to every change)

- **Verify before you rely.** Confirm a package is actually installed before importing it
  (`​.venv/bin/pip show <pkg>`); confirm a tag/column exists in the data before indexing it.
  Do not assume — OSM tags are sparse and pandas fills missing columns with `NaN`.
- **Every line must be justified** algorithmically and mathematically. No dead code, no
  speculative abstraction, no "just in case" branches.
- **No duplication.** Shared logic lives in `osmguide` and is imported. If two notebooks need
  the same helper, it belongs in the package, not copy-pasted.
- **Simplicity over cleverness.** Prefer the most readable correct form. A lesson reader
  should be able to follow the code.
- **Reliability & safety.** Guard against malformed geometry and missing tags (see the
  `is_medical` note below). Treat the `.pbf` as untrusted input: skip degenerate polygons
  rather than crashing.
- **English only.** All code, comments, docstrings, notebook prose, and figure titles must
  be in English.

## Environment

Dependencies live in a project virtualenv at `.venv/` (Python 3.12) and are declared in
`pyproject.toml`. Install the package editable (which also pulls Jupyter via the extra):

```bash
.venv/bin/pip install -e ".[notebooks]"   # core deps + jupyterlab + ipykernel

.venv/bin/python -m osmguide               # smoke test: loads sample data, opens the base map
.venv/bin/jupyter lab                       # run the lessons
```

`python -m osmguide` (`osmguide/__main__.py`) loads the sample data and opens a matplotlib
window; use it to confirm the package works end-to-end.

## Library reference

The package is a two-module pipeline; downstream code assumes **EPSG:3857** throughout.
Indices are *not* here — they are computed in the `topics/<topic>/` notebooks.

```
datasets/my_area.osm.pbf
        │  load_osm_data(pbf_path) → dict      (osmguide.loader)
        ▼
osmguide/loader.py
        │  plot_base_map(data, ax, extra_legend_items) → (fig, ax)   (osmguide.base_map)
        ▼
osmguide/base_map.py
        │  reused by each lesson, which adds its index on top of the returned ax
        ▼
topics/<topic>/<topic>.ipynb
```

### `loader.py` — data layer

`load_osm_data(pbf_path)` runs a two-pass OSM parse (pass 1 collects node locations,
pass 2 resolves way geometry) and returns a `dict` of GeoDataFrames, all in EPSG:3857:

| key | content |
|---|---|
| `"buildings"` | polygon GeoDataFrame with a `"color"` column pre-computed from `BUILDING_COLORS` |
| `"amenities"` | all nodes tagged `amenity` / `shop` / `office` / `leisure` / `healthcare` |
| `"medical_nodes"` | subset of amenities matching `MEDICAL_AMENITIES` |
| `"general_nodes"` | all other amenity nodes |

**Critical:** `is_medical(amenity, healthcare)` uses `isinstance(x, str)` guards. Never
replace this with a plain truthiness check — pandas fills missing tag columns with `NaN`,
and `bool(NaN) == True` would colour every building as medical.

### `base_map.py` — shared rendering

`plot_base_map(data, ax=None, extra_legend_items=None)` draws buildings + nodes + the Esri
World Imagery basemap via `contextily`. Pass an existing `ax` to embed into a subplot grid.
Returns `(fig, ax)`.

### Lesson contract (in `topics/<topic>/` notebooks)

Each index lesson follows the same pattern, so new lessons can be written by copying an
existing topic folder:
1. load with `data = load_osm_data(SAMPLE_PBF)`;
2. compute the index inline from the GeoDataFrames in `data` (every line justified — see
   `topics/indexes/` for a worked medical-accessibility example);
3. call `fig, ax = plot_base_map(data)` for the base layer;
4. add the index visualization on top of the returned `ax`.

The `topics/indexes/` lesson is the reference template (`README.md` + `indexes.ipynb`).

## Key constraints

- OSM ways tagged `amenity=hospital` (or `healthcare=*`) but with **no** `building` tag are
  still captured as building polygons — the loader synthesizes `building = amenity_value`.
- All CRS conversions happen inside `load_osm_data`; downstream code assumes EPSG:3857.
- The basemap tile source is `cx.providers.Esri.WorldImagery`; swap it in `base_map.py`
  if a different provider is needed.
- Datasets in `datasets/` are intentionally small so they can be committed and the guide is
  reproducible offline. Keep new sample data small for the same reason.
