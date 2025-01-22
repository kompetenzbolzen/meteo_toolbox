#!/usr/bin/env python3

import requests
import datetime
import requests
import os
import itertools

import bz2

from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import xarray as xr

from .. import misc
from ..aggregator import Aggregator, Variable, Dimension

from typing import Literal, Union

BASE='https://opendata.dwd.de/weather/nwp'

class IconAggregator(Aggregator):
    PROVIDES = [
        Variable.TEMPERATURE_3D,
        Variable.U_3D,
        Variable.V_3D,
        Variable.U_SURFACE,
        Variable.V_SURFACE,
    ]

    _MAPPING = {
            Variable.TEMPERATURE_3D: {'path': 't', 'data':'t', 'plev': True},
            Variable.U_3D: {'path': 'u', 'data':'u', 'plev': True},
            Variable.V_3D: {'path': 'v', 'data':'v', 'plev': True},
            Variable.U_SURFACE:{'path': 'u_10m', 'data':'u10', 'plev': False},
            Variable.V_SURFACE:{'path': 'v_10m', 'data':'v10', 'plev': False},
            Variable.GUST_SURFACE:{'path': 'vmax_10m', 'data':'fg10', 'plev': False},
    }

    _MODEL_SUFFIX = {
            'icon': 'global',
            'icon-eu': 'europe',
            'icon-d2': 'germany'
    }

    def _init(self):
        self._dataset = None
        self._run = None
        self._date = None

    def _load_config(self, model: Literal['icon', 'icon-eu', 'icon-d2'],
                     pressure_levels: list[int], steps: list[int],
                     description: Union[None,str] = None) -> None:
        self._description = description
        self._model = model
        self._levels = pressure_levels
        self._steps = steps

        self._download_dir = os.path.join(self._cache_dir, self._name)
        misc.create_output_dir(self._download_dir)

        self._caps_in_filename = False if model == 'icon-d2' else True

    def _aggregate(self) -> None:
        self._run, self._date = get_current_run()
        filelist = self._list_needed_files()

        for _ in ThreadPool(cpu_count()).map(download_url, filelist):
            pass

        # TODO bit ugly, eh?
        ds_vars = []
        for var in self._needed_variables:
            ds_steps = []
            for step in self._steps:
                if self._MAPPING[var]['plev']:
                    ds_steps.append(xr.concat(
                            [xr.open_dataset(os.path.join(self._download_dir,f)) for f in [self._construct_filename(step,var,l) for l in self._levels]],
                            dim='icobaricInhPa'
                            ))
                else:
                    ds_steps.append(xr.open_dataset(os.path.join(self._download_dir,self._construct_filename(step,var))))
            ds_vars.append(xr.concat(ds_steps, dim='step'))
        self._dataset = xr.merge(ds_vars)


        # TODO is this needed still?
        if self._description is not None:
            self._dataset.attrs['_description'] = self._description

    def _list_needed_files(self) -> list:
        filelist = []

        for var, step in itertools.product(self._needed_variables, self._steps):
            url_base = f'{BASE}/{self._model}/grib/{self._run}/{self._MAPPING[var]['path']}'
            if self._MAPPING[var]['plev']:
                l =  [self._construct_filename(step, var, l) for l in self._levels]
                filelist += [(f'{url_base}/{f}.bz2', os.path.join(self._download_dir,f)) for f in l]
            else:
                f = self._construct_filename(step, var)
                filelist.append((f'{url_base}/{f}.bz2', os.path.join(self._download_dir,f)))

        return filelist

    def _construct_filename(self, step, var, level = None) -> str:
        run, date = self._run, self._date
        step_str = f'{step:03d}'
        v = self._MAPPING[var]['path']
        v_caps = v.upper() if self._caps_in_filename else v

        if level is not None:
            return '{}_{}_regular-lat-lon_pressure-level_{}{}_{}_{}_{}.grib2'.format(
                self._model, self._MODEL_SUFFIX[self._model],
                date, run, step_str, level, v_caps )
        return '{}_{}_regular-lat-lon_single-level_{}{}_{}_{}.grib2'.format(
            self._model, self._MODEL_SUFFIX[self._model],
            date, run, step_str, v_caps )



    def _query_data(self, var: Variable, query: list[tuple[Variable,object]]) -> xr.DataArray:
        print("Not Implemented")
        return xr.DataArray()

    def _query_dimensions(self, var: Variable) -> list[Dimension]:
        print("Not Implemented")
        return []

def get_current_run():
    # we allow up to 3h of slack for DWD to upload the latest run
    now = datetime.datetime.now(datetime.timezone.utc)
    corrected = now - datetime.timedelta(hours=3)

    run = int(corrected.hour / 6) * 6

    return (f'{run:02d}', corrected.strftime('%Y%m%d'))

def download_url(args):
    url, dest = args

    if os.path.exists(dest):
        return

    r = requests.get(url)
    if not r.ok:
        print(f'Failed Request to download {dest}:\n')
        print(f'URL {url}, {dest}:\n')
        return
    try:
        with open(dest, 'wb') as f:
            f.write(bz2.decompress(r.content))
        print(f'Downloaded {dest}')
    except Exception as e:
        print(f'Failed to download {dest}:\n', e)

def clean_output_dir(directory, target):
    to_delete = [f for f  in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if target in to_delete:
        del to_delete[to_delete.index(target)]

    for f in to_delete:
        os.unlink(os.path.join(directory, f))

def test():
    a = IconAggregator(cache_dir='./asdf')
    a.load_config(
            model='icon-eu', name='test', pressure_levels = [1000,850,500],
            steps = [0,3,6,9,12,15,18,21,24])
    a.add_needed(Variable.U_3D)
    a.add_needed(Variable.V_3D)
    a.add_needed(Variable.U_SURFACE)
    a.add_needed(Variable.V_SURFACE)

    a.aggregate()
    print(a._dataset)
