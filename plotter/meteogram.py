#!/usr/bin/env python3
import os
import json

import matplotlib.pyplot as plt

import xarray as xr
from metpy.interpolate import cross_section
import metpy.calc as mpcalc
from metpy.units import units

import misc

def run(data, plots, output='.'):
    misc.create_output_dir(output)
    index = []

    for plot in plots:
        index.append(_plot(data, output, **plot))

    return index

def _plot(data, output, name, lat, lon):
    index = []

    data = data.sel(latitude=lat, longitude = lon, method='nearest')

    #data = data.assign_coords(step=(data.step / (10**9 * 3600)))
    data = data.assign_coords(step=(data.step.values.astype(float) * units('ns')).to('hour'))

    init = misc.np_time_convert(data.time.values)

    init_str = init.strftime('%d %b %Y - %HUTC')
    init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

    fig = plt.figure(figsize=(10, 10), layout="constrained")


    # start figure and set axis
    ax = fig.add_subplot(5,1,(1,2))

    ax.set_ylabel('Pressure level [hPa]')

    #clc = ax.plot(data.step.values.astype('float64'), data.isobaricInhPa, data.ccl.transpose())
    #clc = ax.imshow(data.ccl.transpose(), extent=(data.step.values.astype(float).min(), data.step.values.astype(float).max(), data.isobaricInhPa.min(), data.isobaricInhPa.max()), aspect='auto', cmap='Blues_r', vmin=0, vmax=100)
    #plt.colorbar(clc, label='clcov')
    # Blues_r
    clc = ax.contourf(data.step, data.isobaricInhPa, data.ccl.transpose(), cmap='clcov', vmin=0, vmax=100, levels=9)

    # use Format parameter for n/8
    plt.colorbar(clc, label='cloudcov', extendfrac=None, ticks=[100*n/8 for n in range(9)], format=lambda x,_: f'{int(x/12.5)}/8', pad=0.0, fraction=0.015)


    cf = ax.contour(data.step, data.isobaricInhPa, data.t.metpy.convert_units('degC').transpose())
    ax.clabel(cf, inline=True, fontsize=10)
    #plt.colorbar(cf, pad=0, aspect=50)
    #plt.colorbar(cf)

    barbs = ax.barbs(data.step, data.isobaricInhPa, data.u.transpose(), data.v.transpose())
    #ax.barbs(data.u, data.v, color='black', length=5, alpha=0.5)

    ax.invert_yaxis()

    ### Second plot

    ax2 = fig.add_subplot(5,1,3,sharex=ax)
    ax2.plot(data.step, data.t2m.metpy.convert_units('degC').transpose(), color='red', label='Temperature (2m)')
    ax2.plot(data.step, mpcalc.dewpoint_from_relative_humidity(data.t2m, data.r2).transpose(), color='blue', label='Dewpoint (2m)')
    ax2.set_ylabel('Temperature [degC]')
    ax2.legend(loc='lower right')

    outname = f'{name}_{init_for_filename}.png'
    plt.savefig(os.path.join(output, outname))
    plt.close('all')

    index.append(
        {
            'file': outname,
            'init': init_str,
            'valid': init_str,
            'valid_offset': '00'
        }
    )

    with open(os.path.join(output, f'{name}.index.json'), 'w') as f:
        f.write(json.dumps(index, indent=4))

    return { 'name': name, 'indexfile': f'{name}.index.json' }
