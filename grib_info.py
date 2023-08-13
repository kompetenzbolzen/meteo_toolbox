#!/usr/bin/env python3
import pygrib
import sys

grib = pygrib.open(sys.argv[1])
for grb in grib:
    print(sys.argv[1], grb)
