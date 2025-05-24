#!/usr/bin/env python3
import os

import datetime
import json

import matplotlib.pyplot as plt

import xarray as xr
from metpy.units import units
import metpy.calc as mpcalc
import numpy as np

from .. import skewt
from .. import misc

from . import Plotter
from ..aggregator import Variable, Dimension, DataView


class Skewt(Plotter):
    def _load_config(self, **kwargs):
        print(kwargs)
        self._cfg = kwargs

    def _report_needed_variables(self) -> list[Variable]:
        return [
            Variable.U_3D, Variable.V_3D,
            Variable.TEMPERATURE_3D,
            Variable.HUMIDITY_3D,
        ]

    def _plot(self, view):
        _plot(view.get(), self._cache_dir, view.name)

def _plot(data, output, name, analysis=None):
    p = data[Dimension.PRESSURE].values * units.hPa
    T = data[Variable.TEMPERATURE_3D].values * units.K
    relHum = data[Variable.HUMIDITY_3D].values * units.percent
    Td = mpcalc.dewpoint_from_relative_humidity(T, relHum)
    u = data[Variable.U_3D].values * (units.m / units.s)
    v = data[Variable.V_3D].values * (units.m / units.s)

    valid = misc.np_time_convert(data[Dimension.TIME].values)
    init = misc.np_time_convert(data[Dimension.INIT_TIME].values)

    valid_str = valid.strftime('%d %b %Y - %HUTC')
    init_str = init.strftime('%d %b %Y - %HUTC')
    hours_since_init_str = str(int((valid-init) / np.timedelta64(1,'h'))).zfill(2)

    # TODO fix description
    skt = skewt.Skewt(p=p, T=T, Td=Td)
    skt.addWindUV(u, v)
    skt.addInfo(f'{name} INIT+' + hours_since_init_str)
    skt.addInfo(f"VALID: {valid_str}")
    skt.addInfo(f"INIT : {init_str}")
    #skt.addInfo(f"LAT {lat} LON {lon}")

    if analysis is not None:
        skt.addAnalysis(shade=True, analysis=analysis)

    if '_description' in data.attrs:
        skt.addInfo(data.attrs['_description'])

    init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

    outname = f'skewt_{name}_{init_for_filename}+{hours_since_init_str}.png'
    skt.plot(filename=os.path.join(output, outname))

    plt.close('all')
