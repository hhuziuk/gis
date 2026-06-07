"""End-to-end smoke test: ``python -m osmguide`` loads the sample data and
opens the satellite-backed base map in a matplotlib window."""

import matplotlib.pyplot as plt

from osmguide import SAMPLE_PBF, load_osm_data, plot_base_map

data = load_osm_data(SAMPLE_PBF)
plot_base_map(data)
plt.show()
