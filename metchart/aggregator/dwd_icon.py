#!/usr/bin/env python3

import requests
import datetime
import requests
import os
import itertools

import cfgrib

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

    def _load_config(self, model: Literal['icon', 'icon-eu', 'icon-d2'],
                     name: str, pressure_levels: list[int], steps: list[int],
                     description: Union[None,str] = None) -> None:
        self._name = name
        self._description = description
        self._model = model
        self._levels = pressure_levels
        self._steps = steps

        self._download_dir = os.path.join(self._cache_dir, self._name)
        misc.create_output_dir(self._download_dir)

        self._caps_in_filename = False if model == 'icon-d2' else True

    def _aggregate(self) -> None:
        run, date = get_current_run()
        filelist = self._list_needed_files(run, date)

        for _ in ThreadPool(cpu_count()).map(download_url, filelist):
            pass

        # NOTE open_mfdataset needs dask. do we want that?
        _, gribs = zip(*filelist)
        gribs = list(gribs)
        #self._dataset = xr.open_mfdataset(gribs, engine='cfgrib', coords='all')
        #self._dataset = xr.open_mfdataset(list(gribs), engine='cfgrib', drop_variables='heightAboveGround', coords='different')

        # TODO Concat alon dimensions manually
        # 1. along pressure (only for plev)
        # 2. along step
        # 3. merge variables together
        # Check, if memory use is OK!
        self._dataset = xr.concat(
                [xr.open_dataset(g,drop_variables='heightAboveGround') for g in gribs],
                'step',
                coords='minimal'
                )

        # TODO is this needed still?
        if self._description is not None:
            self._dataset.attrs['_description'] = self._description

    def _list_needed_files(self, run, date) -> list:
        filelist = []

        for step, level, var in itertools.product(
                [f'{s:03d}' for s in self._steps],
                self._levels,
                [v for v in self._needed_variables if self._MAPPING[v]['plev']] ):
            v = self._MAPPING[var]['path']
            v_caps = v.upper() if self._caps_in_filename else v
            filename = '{}_{}_regular-lat-lon_pressure-level_{}{}_{}_{}_{}.grib2'.format(
                       self._model, self._MODEL_SUFFIX[self._model],
                       date, run, step, level, v_caps )
            URL = f'{BASE}/{self._model}/grib/{run}/{v}/{filename}.bz2'

            filelist.append((URL, os.path.join(self._download_dir, filename)))

        for step, var in itertools.product(
                [f'{s:03d}' for s in self._steps],
                [v for v in self._needed_variables if not self._MAPPING[v]['plev']] ):
            v = self._MAPPING[var]['path']
            v_caps = v.upper() if self._caps_in_filename else v
            filename = '{}_{}_regular-lat-lon_single-level_{}{}_{}_{}.grib2'.format(
                       self._model, self._MODEL_SUFFIX[self._model],
                       date, run, step, v_caps )
            URL = f'{BASE}/{self._model}/grib/{run}/{v}/{filename}.bz2'

            filelist.append((URL, os.path.join(self._download_dir, filename)))

        return filelist

    def _query_data(self, var: Variable, query: list[tuple[Variable,object]]) -> xr.DataArray:
        return xr.DataArray()

    def _query_dimensions(self, var: Variable) -> list[Dimension]:
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
