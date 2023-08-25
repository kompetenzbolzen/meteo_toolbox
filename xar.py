#!/usr/bin/env python3

import xarray as xr
from metpy.units import units
import metpy.calc as mpcalc

import numpy as np

import datetime

import skewt

def np_time_convert(dt64):
    unix_epoch = np.datetime64(0, 's')
    one_second = np.timedelta64(1, 's')
    seconds_since_epoch = (dt64 - unix_epoch) / one_second

    return datetime.datetime.utcfromtimestamp(seconds_since_epoch)

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

    valid = np_time_convert(step.valid_time.values)
    init = np_time_convert(step.time.values)

    valid_str = valid.strftime('%d %b %Y - %HUTC')
    init_str = init.strftime('%d %b %Y - %HUTC')
    hours_since_init_str = str(int(this_step.step.values / np.timedelta64(1,'h'))).zfill(2)

    skt = skewt.Skewt(p=p, T=T, Td=Td)
    skt.addWindUV(u, v)
    skt.addInfo(f"VALID: {valid_str}")
    skt.addInfo(f"INIT : {init_str}")
    skt.addInfo(f"LAT {lat} LON {lon}")
    skt.addInfo('INIT+' + hours_since_init_str)
    skt.addInfo(f'')
    skt.addAnalysis(shade=True, analysis='lcl')
    skt.addInfo("DWD ICON-D2")

    init_for_filename = init.strftime('%Y-%m-%d-%H')

    skt.plot(filename=f'skewt_{init_for_filename}+{hours_since_init_str}.png')
