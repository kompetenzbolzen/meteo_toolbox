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
        Variable.HUMIDITY_3D,
        Variable.TEMPERATURE_SURFACE,
        Variable.HUMIDITY_SURFACE,
        Variable.GEOPOTENTIAL,

        Variable.U_3D,
        Variable.V_3D,
        Variable.U_SURFACE,
        Variable.V_SURFACE,
        Variable.GUST_SURFACE,

        Variable.CLOUDCOVER_3D,
        Variable.PRECIPITATION_ACCUMULATED,
        Variable.SNOW_DEPTH,

        Variable.CONVECTION_WET_BASE,
        Variable.CONVECTION_WET_TOP,
        Variable.CONVECTION_DRY_TOP,

        Variable.CAPE,
        Variable.CIN,

        Variable.PRESSURE_SEA_LEVEL,
    ]

    _VAR_MAPPING = {
            Variable.TEMPERATURE_3D: {'path': 't', 'data':'t', 'plev': True},
            Variable.HUMIDITY_3D: {'path': 'relhum', 'data':'r', 'plev': True},
            Variable.TEMPERATURE_SURFACE: {'path': 't_2m', 'data':'t2m', 'plev': False},
            Variable.HUMIDITY_SURFACE: {'path': 'relhum_2m', 'data':'r2', 'plev': False},
            Variable.GEOPOTENTIAL: {'path': 'fi', 'data':'z', 'plev': True},

            Variable.U_3D: {'path': 'u', 'data':'u', 'plev': True},
            Variable.V_3D: {'path': 'v', 'data':'v', 'plev': True},
            Variable.U_SURFACE:{'path': 'u_10m', 'data':'u10', 'plev': False},
            Variable.V_SURFACE:{'path': 'v_10m', 'data':'v10', 'plev': False},
            Variable.GUST_SURFACE:{'path': 'vmax_10m', 'data':'max_i10fg', 'plev': False},

            Variable.CLOUDCOVER_3D: {'path': 'clc', 'data':'ccl', 'plev': True},
            Variable.PRECIPITATION_ACCUMULATED: {'path': 'tot_prec', 'data':'tp', 'plev': False},
            Variable.SNOW_DEPTH: {'path': 'h_snow', 'data':'sde', 'plev': False},

            Variable.CONVECTION_WET_BASE: {'path': 'hbas_con', 'data':'HBAS_CON', 'plev': False},
            Variable.CONVECTION_WET_TOP:  {'path': 'htop_con', 'data':'HTOP_CON', 'plev': False},
            Variable.CONVECTION_DRY_TOP:  {'path': 'htop_dc',  'data':'HTOP_DC',  'plev': False},

            Variable.CAPE: {'path': 'cape_ml', 'data':'CAPE_ML', 'plev': False},
            Variable.CIN: {'path': 'cin_ml', 'data':'CIN_ML', 'plev': False},

            Variable.PRESSURE_SEA_LEVEL:  {'path': 'pmsl',  'data':'prmsl',  'plev': False},

            Dimension.PRESSURE:{'data': 'isobaricInhPa'},
            Dimension.INIT_TIME:{'data': 'time'},
            Dimension.TIME:{'data': 'step'},
    }

    _DIM_MAPPING = {
            # NOTE lat/lon are already the right name
            # Dimension.LATITUDE: 'latitude',
            # Dimension.LONGITUDE: 'longitude',
            # NOTE: see set_index in _aggregate() to see how this works...
            Dimension.TIME: 'step',
            # TODO pressure, time
            # These are non-indexed dimensions, so not queryable
            # see: https://github.com/pydata/xarray/issues/2028
            Dimension.PRESSURE: 'isobaricInhPa',
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

        load_defaults={
                'drop_variables':['heightAboveGround'],
                'decode_timedelta': False,
        }

        # TODO bit ugly, eh?
        ds_vars = []
        for var in self._needed_variables:
            ds_steps = []
            for step in self._steps:
                if self._VAR_MAPPING[var]['plev']:
                    ds_steps.append(xr.concat(
                            [
                                xr.open_dataset(os.path.join(self._download_dir,f), **load_defaults)
                                for f in [self._construct_filename(step,var,l) for l in self._levels]
                            ],
                            dim='isobaricInhPa'
                        ))
                else:
                    ds_steps.append(
                            xr.open_dataset(
                                os.path.join(self._download_dir,self._construct_filename(step,var)),
                                **load_defaults
                            )
                        ) # NOTE Maybe a bit hacky, but does the job
            ds_vars.append(xr.concat(ds_steps, dim='step'))
        self._dataset = xr.merge(ds_vars)


        # TODO is this needed still?
        if self._description is not None:
            self._dataset.attrs['_description'] = self._description

        self._dataset = self._dataset.set_index(step='valid_time')
        self._dataset = self._dataset.rename_vars(
            { v['data']: k for k, v in self._VAR_MAPPING.items() if v['data'] in self._dataset }
        )
        self._dataset = self._dataset.rename_dims(
            { v: k for k, v in self._DIM_MAPPING.items() if v in self._dataset }
        )

    def _list_needed_files(self) -> list:
        filelist = []

        for var, step in itertools.product(self._needed_variables, self._steps):
            url_base = f'{BASE}/{self._model}/grib/{self._run}/{self._VAR_MAPPING[var]['path']}'
            if self._VAR_MAPPING[var]['plev']:
                l =  [self._construct_filename(step, var, l) for l in self._levels]
                filelist += [(f'{url_base}/{f}.bz2', os.path.join(self._download_dir,f)) for f in l]
            else:
                f = self._construct_filename(step, var)
                filelist.append((f'{url_base}/{f}.bz2', os.path.join(self._download_dir,f)))

        return filelist

    def _construct_filename(self, step, var, level = None) -> str:
        run, date = self._run, self._date
        step_str = f'{step:03d}'
        v = self._VAR_MAPPING[var]['path']
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
