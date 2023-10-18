#!/usr/bin/env python3
import os

import datetime
import json

import xarray as xr
from metpy.units import units
import metpy.calc as mpcalc
import numpy as np

import skewt

import misc

config = {
    'source':'dwd_icon-eu/combined.grib2',
    'plots':[
        {
            'lat':47.9626,
            'lon':11.9964,
            'name':'Antersberg',
            'analysis':'lcl'
        },
    ]
}

def run(data, plots, output='.'):
    misc.create_output_dir(output)
    index = []

    for plot in plots:
        index.append(_plot(data, output, **plot))

    return index

def _plot(data, output, lat, lon, name, analysis=None):
    for_temp = data.sel(latitude=lat, longitude = lon, method='nearest')
    for_temp = for_temp[['r', 't', 'u', 'v']]
    index = []

    for step in for_temp.coords['step']:
        this_step = for_temp.sel(step=step)

        p = this_step.coords['isobaricInhPa'].values * units.hPa
        T = this_step.t.values * units.K
        relHum = this_step.r.values * units.percent
        Td = mpcalc.dewpoint_from_relative_humidity(T, relHum)
        u = this_step.u.values * (units.m / units.s)
        v = this_step.v.values * (units.m / units.s)

        valid = misc.np_time_convert(step.valid_time.values)
        init = misc.np_time_convert(step.time.values)

        valid_str = valid.strftime('%d %b %Y - %HUTC')
        init_str = init.strftime('%d %b %Y - %HUTC')
        hours_since_init_str = str(int(this_step.step.values / np.timedelta64(1,'h'))).zfill(2)

        skt = skewt.Skewt(p=p, T=T, Td=Td)
        skt.addWindUV(u, v)
        skt.addInfo(f'{name} INIT+' + hours_since_init_str)
        skt.addInfo(f"VALID: {valid_str}")
        skt.addInfo(f"INIT : {init_str}")
        skt.addInfo(f"LAT {lat} LON {lon}")

        if analysis is not None:
            skt.addAnalysis(shade=True, analysis=analysis)

        # TODO get from source!
        skt.addInfo("FORECAST DWD ICON-D2")

        init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

        outname = f'skewt_{name}_{init_for_filename}+{hours_since_init_str}.png'
        skt.plot(filename=os.path.join(output, outname))

        index.append(
            {
                'file': outname,
                'init': init_str,
                'valid': valid_str,
                'valid_offset': hours_since_init_str
            }
        )

    with open(os.path.join(output, f'skewt_{name}.index.json'), 'w') as f:
        f.write(json.dumps(index, indent=4))

    return {'name': name, 'indexfile': f'skewt_{name}.index.json'}

if __name__ == '__main__':
    run(**config)
