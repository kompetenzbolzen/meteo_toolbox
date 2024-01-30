#!/usr/bin/env python3

import sys
import yaml
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

from metpy.units import units

def create_aggregators(cfg):
    ret = {}
    for aggregator in cfg:
        aggconf = cfg[aggregator]
        classname = aggconf['module']
        del aggconf['module']

        module = __import__(classname, fromlist=[None])

        ret[aggregator] = module.load_data(name=aggregator, **aggconf)

    return ret

mpl.use('agg')

# Define custom gpm and gpdm units. The default gpm in metpy is aliased to meter.
# We need the correct definition
units.define('_gpm = 9.80665 * J/kg')
units.define('_gpdm = 10 * _gpm')

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

FILE = 'config.yaml'
if len(sys.argv) > 1:
    FILE = sys.argv[1]

conf = None
with open(FILE, 'r') as f:
    conf = yaml.safe_load(f)

aggregators = create_aggregators(conf['aggregator'])

index = []

for plotter in conf['plotter']:
    modname = plotter['module']
    del plotter['module']

    if 'aggregator' in plotter:
        plotter['data'] = aggregators[plotter['aggregator']]
        del plotter['aggregator']

    mod = __import__(modname, fromlist=[None])
    index.extend(mod.run(**plotter))

    plt.close('all')

with open(conf['index'], 'w') as f:
    f.write(json.dumps(index, indent=4))
