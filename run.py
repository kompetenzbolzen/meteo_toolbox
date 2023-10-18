#!/usr/bin/env python3

import sys
import yaml
import json
import matplotlib.pyplot as plt

from metpy.units import units

# Define custom gpm and gpdm units. The default gpm in metpy is aliased to meter.
# We need the correct definition
units.define('_gpm = 9.80665 * J/kg')
units.define('_gpdm = 10 * _gpm')

FILE = 'config.yaml'
if len(sys.argv) > 1:
    FILE = sys.argv[1]

conf = None
with open(FILE, 'r') as f:
    conf = yaml.safe_load(f)

index = []

for plotter in conf['plotter']:
    modname = plotter['module']
    del plotter['module']

    if 'aggregator' in plotter:
        aggname = plotter['aggregator']
        del plotter['aggregator']
        aggconf = conf['aggregator'][aggname]
        classname = aggconf['module']
        # We should prbly not delete it like in the plotter, since it is not a deepcopy
        # and may be used again.

        agg = __import__(classname, fromlist=[None])

        # TODO: figure out a way to use **aggconf instead.
        plotter['data'] = agg.load_data(aggname, aggconf)

    mod = __import__(modname, fromlist=[None])
    index.extend(mod.run(**plotter))

    plt.close('all')

with open(conf['index'], 'w') as f:
    f.write(json.dumps(index, indent=4))
