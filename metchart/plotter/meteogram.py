#!/usr/bin/env python3
import os
import json

import numpy as np

import matplotlib.pyplot as plt

import metpy.calc as mpcalc

from ..aggregator import Variable, Dimension, DataView
from . import Plotter

from .. import misc

HEIGHT = 13

class Meteogram(Plotter):
    def _load_config(self, **kwargs):
        print(kwargs)
        self._cfg = kwargs

    def _report_needed_variables(self) -> list[Variable]:
        return [
            Variable.U_SURFACE, Variable.V_SURFACE, Variable.GUST_SURFACE,
            Variable.U_3D, Variable.V_3D,
            Variable.TEMPERATURE_3D, Variable.TEMPERATURE_SURFACE,
            Variable.HUMIDITY_3D, Variable.HUMIDITY_SURFACE,
            Variable.PRECIPITATION_ACCUMULATED, Variable.SNOW_DEPTH,
            Variable.CLOUDCOVER_3D,
            Variable.PRESSURE_SEA_LEVEL,
            Variable.CONVECTION_WET_TOP, Variable.CONVECTION_WET_BASE,
        ]

    def _plot(self, view):
        _plot(view.get(), self._cache_dir, view.construct_full_name())

def run(data, plots, output='.', name='meteogram'):
    misc.create_output_dir(output)
    index = []

    for plot in plots:
        index.append(_plot(data, output, **plot))

    with open(os.path.join(output, f'{name}.index.json'), 'w') as f:
        f.write(json.dumps(index, indent=4))

    return [{ 'name': name, 'indexfile': f'{name}.index.json', 'list_title': 'Location' }]

def _get_next_subplot(size, counter=0):
    ret = (counter + 1, counter + size)
    counter += size
    return counter, ret

def _add_cloudcov(ax, data):
    ax.set_ylabel('Pressure level [hPa]')

    clc = ax.contourf(data[Dimension.TIME], data[Dimension.PRESSURE], data[Variable.CLOUDCOVER_3D].transpose(), cmap='clcov', vmin=0, vmax=100, levels=9)

    # use Format parameter for n/8
    plt.colorbar(clc, label='cloudcov', extendfrac=None, ticks=[100*n/8 for n in range(9)], format=lambda x,_: f'{int(x/12.5)}/8', pad=0.0, fraction=0.015)

    cf = ax.contour(data[Dimension.TIME], data[Dimension.PRESSURE], data[Variable.TEMPERATURE_3D].metpy.convert_units('degC').transpose())
    ax.clabel(cf, inline=True, fontsize=10)

    ax.barbs(
            data[Dimension.TIME],
            data[Dimension.PRESSURE],
            data[Variable.U_3D].metpy.convert_units('kt').transpose(),
            data[Variable.V_3D].metpy.convert_units('kt').transpose()
        )

    ax.invert_yaxis()

def _add_temp_dewpoint(ax, data):
    ### Temp + Dewpoint
    ax.plot(data[Dimension.TIME], data[Variable.TEMPERATURE_SURFACE].metpy.convert_units('degC').transpose(), color='red', label='Temperature (2m)')
    ax.plot(data[Dimension.TIME], mpcalc.dewpoint_from_relative_humidity(data[Variable.TEMPERATURE_SURFACE], data[Variable.HUMIDITY_SURFACE]).transpose(), color='blue', label='Dewpoint (2m)')
    ax.plot(data[Dimension.TIME], data.sel(**{Dimension.PRESSURE:850.0})[Variable.TEMPERATURE_3D].metpy.convert_units('degC').transpose(), color='grey', label='Temperature (850hPa)')
    ax.set_ylabel('Temperature [degC]')
    ax.legend(loc='lower right')

def _add_mslp(ax, data):
    ax.plot(data[Dimension.TIME], data[Variable.PRESSURE_SEA_LEVEL].metpy.convert_units('hPa').transpose(), color='black', label='Temperature (2m)')
    ax.set_ylabel('Mean Sea Level Pressure [hPa]')

def _add_convective_clouds(ax, data):
    # TODO: ADD HBAS_CON, HTOP_CON
    # If none: -500m
    ax.set_ylim(0, 14)
    ax.set_ylabel('Convective Clouds Height [km]')
    ax.bar(data[Dimension.TIME], alpha=0.5,
            bottom=data[Variable.CONVECTION_WET_BASE].metpy.convert_units('km').transpose(),
            height=(data[Variable.CONVECTION_WET_TOP].metpy.convert_units('km')-data[Variable.CONVECTION_WET_BASE].metpy.convert_units('km')).transpose(),
            align='edge', width=np.timedelta64(3, 'h'))

def _add_precip(ax, data):
    ax.set_ylabel('Total precipitation [mm]')
    ax.set_ylim(0, 30)
    ax.bar(data[Dimension.TIME][:-1], data[Variable.PRECIPITATION_ACCUMULATED].diff('step').transpose(), width=np.timedelta64(3, 'h'),
            align='edge', alpha=0.7, color='green')

    ax_p = ax.twinx()
    ax_p.set_ylabel('Snow depth [m]')
    ax_p.set_ylim(bottom=0)
    ax_p.plot(data[Dimension.TIME], data[Variable.SNOW_DEPTH].transpose(), color='blue')

def _add_surface_wind(ax, data):
    ax.plot(data[Dimension.TIME],
            mpcalc.wind_speed(data[Variable.U_SURFACE].transpose(), data[Variable.V_SURFACE].transpose()),
            color='black', label='Wind (10m)')
    ax.plot(data[Dimension.TIME], data[Variable.GUST_SURFACE].transpose(), color='red', label='Gust (10m)')

    ax_b = ax.twinx()
    ax_b.barbs(
            data[Dimension.TIME],
            [1 for _ in data[Dimension.TIME]],
            data[Variable.U_SURFACE].metpy.convert_units('kt').transpose(),
            data[Variable.V_SURFACE].metpy.convert_units('kt').transpose()
        )
    ax_b.axis('off')

    ax.set_ylabel('Wind Speed [m/s]')
    ax.legend(loc='lower right')

def _plot(data, output, name):
    fig = plt.figure(figsize=(12, 12), layout="constrained")

    sp_cnt, spec = _get_next_subplot(4)
    ax = fig.add_subplot(HEIGHT,1,spec)
    _add_cloudcov(ax, data)

    sp_cnt, spec2 = _get_next_subplot(2,sp_cnt)
    ax2 = fig.add_subplot(HEIGHT,1,spec2,sharex=ax)
    _add_temp_dewpoint(ax2, data)

    sp_cnt, spec3 = _get_next_subplot(2,sp_cnt)
    ax3 = fig.add_subplot(HEIGHT,1,spec3,sharex=ax)
    #ax3.legend(loc='lower right')
    _add_mslp(ax3, data)

    ax4 = ax3.twinx()
    _add_convective_clouds(ax4, data)

    sp_cnt, spec4 = _get_next_subplot(2,sp_cnt)
    ax5 = fig.add_subplot(HEIGHT,1,spec4,sharex=ax)
    _add_precip(ax5, data)

    sp_cnt, spec5 = _get_next_subplot(2,sp_cnt)
    ax6 = fig.add_subplot(HEIGHT,1,spec5,sharex=ax)
    _add_surface_wind(ax6, data)

    ### Info Lines
    sp_cnt, spec5 = _get_next_subplot(1,sp_cnt)
    ax_text = fig.add_subplot(HEIGHT, 1, spec5)

    info_lines = []
    init = misc.np_time_convert(data.init_time.values)
    init_str = init.strftime('%d %b %Y - %HUTC')
    init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

    info_lines.append(f'{name}')
    info_lines.append(f"INIT : {init_str}")
    # TODO reactivate
    #info_lines.append(f"LAT {lat} LON {lon}")

    if '_description' in data.attrs:
        info_lines.append(data.attrs['_description'])

    ax_text.text(0, 0, '\n'.join(info_lines), ha='left', va='center',
            size=10, fontfamily='monospace')
    ax_text.axis("off")

    ### Output

    outname = f'{name}.png'
    plt.savefig(os.path.join(output, outname))
    plt.close('all')

    return (
        {
            'file': outname,
            'init': init_str,
            'valid': init_str,
            'valid_offset': '00',
            'display_name': name,
            'id': name
        })
