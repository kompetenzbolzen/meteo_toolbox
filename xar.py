#!/usr/bin/env python3

import xarray as xr
from metpy.units import units
import metpy.calc as mpcalc

import skewt

#grib = pygrib.open('dwd_icon-d2/combined.grib2')
data = xr.load_dataset('dwd_icon-d2/combined.grib2', engine='cfgrib')

lat = 47.9626
lon = 11.9964

for_temp = data.sel(latitude=lat, longitude = lon, method='nearest')

for_temp = for_temp[['r', 't', 'u', 'v']]

for step in for_temp.coords['step']:
    this_step = for_temp.sel(step=step)

    p = this_step.coords['isobaricInhPa'].values * units.hPa
    T = this_step.t.values * units.K
    relHum = this_step.r.values * units.percent
    Td = mpcalc.dewpoint_from_relative_humidity(T, relHum)
    u = this_step.u.values * (units.m / units.s)
    v = this_step.v.values * (units.m / units.s)

    skt = skewt.Skewt(p=p, T=T, Td=Td)
    skt.addWindUV(u, v)
    skt.addInfo("TEST")
    skt.plot(filename=f'skewt.png')

    break
