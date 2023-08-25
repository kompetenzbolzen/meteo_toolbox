#!/usr/bin/env python3
import pygrib

# http://opendata.dwd.de/weather/nwp/icon-d2/grib/00/t/icon-d2_germany_regular-lat-lon_pressure-level_2023080200_000_1000_t.grib2.bz2

# <BASE>/<RUN>/<PARAMETER>/icon-d2_regular-lat-lon_pressure-level_<INIT>_<OFFSET>_<LEVEL>_<PARAMETER>

GRIBDIR='dwd_icon-d2'

# Flugplatz Saal a. d. Saale
target_lat='50.3108796'
target_lon='10.0646952'

# Find nearest coords in model
# TODO

grib = pygrib.open('dwd_icon-d2/combined.grib2')

# GRIB-Objekt wichtige attribute:
# analDate
# validDate
# units
# level
# typeOfLevel
# name
# shortName

for grb in grib:
    #print(grb)
    vals = grb.values

    lats, lons = grb.latlons()

    for k in grb.keys():
        print(k)

    print(grb.analDate)
    print(grb.validDate)
    print(grb.units)
    print(grb.typeOfLevel)
    break

    # TODO Data in xarray?

    print(grb.name)
    print(grb.level)

    #print('lats min/max: ', lats.shape, lats.max(), lats.min())
    #print('lons min/max: ', lons.shape, lons.max(), lons.min())

    #print(vals.shape)

    #print(vals[100][::100])

    #print(grb.latlons())

