#!/usr/bin/env python3

import sys
import matplotlib as mpl

import logging

from . import customization
from . import manager

def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s | %(levelname)s | %(name)s - %(message)s',
                        datefmt='%c')

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('findlibs').setLevel(logging.WARNING)
    logging.getLogger('cfgrib').setLevel(logging.WARNING)
    logging.getLogger('gribapi').setLevel(logging.WARNING)
    logging.getLogger('metpy').setLevel(logging.WARNING)

    mpl.use('agg')

    customization.register_units()
    customization.register_colormaps()

    FILE = 'examples/config.yaml'
    if len(sys.argv) > 1:
        FILE = sys.argv[1]

    cfg = manager.Manager(FILE)
    cfg.aggregate_data()
    cfg.run_plotters()


if __name__ == '__main__':
    main()
