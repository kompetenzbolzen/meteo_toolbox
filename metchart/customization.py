from metpy.units import units

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

def register_colormaps():
    # Define custom colormap
    clcov_cmap = {
        'red': (
            (0.0, 0.0, 0.0),
            (0.1, 0.9, 0.9),
            (1.0, 0.3, 0.3),
        ),
        'green': (
            (0.0, 0.5, 0.5),
            (0.1, 0.9, 0.9),
            (1.0, 0.3, 0.3),
        ),
        'blue': (
            (0.0, 0.9, 0.9),
            (0.1, 0.9, 0.9),
            (1.0, 0.3, 0.3),
        ),
    }

    mpl.colormaps.register(LinearSegmentedColormap('clcov', clcov_cmap))

def register_units():
    # Define custom gpm and gpdm units. The default gpm in metpy is aliased to meter.
    # We need the correct definition
    units.define('_gpm = 9.80665 * J/kg')
    units.define('_gpdm = 10 * _gpm')
