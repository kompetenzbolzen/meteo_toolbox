#!/usr/bin/env python3

import sys
import yaml
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

for plotter in conf['plotter']:
    modname = plotter['module']
    del plotter['module']

    mod = __import__(modname)
    mod.run(**plotter)

    plt.close('all')
