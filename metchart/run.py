#!/usr/bin/env python3

import sys
import matplotlib as mpl

from . import customization
from . import manager

def main():
    mpl.use('agg')

    customization.register_units()
    customization.register_colormaps()

    FILE = 'examples/config.yaml'
    if len(sys.argv) > 1:
        FILE = sys.argv[1]

    cfg = manager.Manager(FILE)
    cfg.run_plotters()


if __name__ == '__main__':
    main()
