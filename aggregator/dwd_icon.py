#!/usr/bin/env python3

import requests
import datetime
import pytz
import requests
import os

from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import subprocess

import xarray as xr

import misc

BASE='https://opendata.dwd.de/weather/nwp'

def get_current_run():
    # we allow up to 3h of slack for DWD to upload the latest run
    tz = pytz.timezone('UTC')
    now = datetime.datetime.now(datetime.timezone.utc)
    corrected = now - datetime.timedelta(hours=3)

    run = int(corrected.hour / 6) * 6

    return (f'{run:02d}', corrected.strftime('%Y%m%d'))

def download_url(args):
    url, dest = args
    r = requests.get(url)
    try:
        with open(dest, 'wb') as f:
            f.write(r.content)
        print(f'Downloaded {dest}')
    except Exception as e:
        print(f'Failed to download {dest}:\n', e)

def unpack_bz2(dest):
    res = subprocess.run(['bzip2', '-df', dest])
    if res.returncode != 0:
        print(f'There was an error unpacking {dest}:', res.stderr)

def download_dwd_gribs(
        date, run, target, output, model, steps, model_long,
        pressure_level_parameters, parameter_caps_in_filename,
        single_level_parameters, pressure_levels
):
    misc.create_output_dir(output)

    to_download = []

    for step in steps:
        step_str = f'{step:03d}'

        for parameter in pressure_level_parameters:
            parameter2 = parameter.upper() if parameter_caps_in_filename else parameter

            for level in pressure_levels:
                filename = f'{model_long}_regular-lat-lon_pressure-level_{date}{run}_{step_str}_{level}_{parameter2}.grib2.bz2'
                URL = f'{BASE}/{model}/grib/{run}/{parameter}/{filename}'

                to_download.append((URL, os.path.join(output, filename)))

        for parameter in single_level_parameters:
            parameter2 = parameter.upper() if parameter_caps_in_filename else parameter
            filename = f'{model_long}_regular-lat-lon_single-level_{date}{run}_{step_str}_{parameter2}.grib2.bz2'
            URL = f'{BASE}/{model}/grib/{run}/{parameter}/{filename}'

            to_download.append((URL, os.path.join(output, filename)))


    for _ in ThreadPool(cpu_count()).imap_unordered(download_url, to_download):
        pass

    print('Done Downloading. Uncompressing...')

    for _ in ThreadPool(cpu_count()).imap_unordered(unpack_bz2, [dest for _, dest in to_download]):
        pass

    downloaded_gribs = [dest.removesuffix('.bz2') for _, dest in to_download]

    res = subprocess.run(['grib_copy'] + downloaded_gribs + [target])
    if res.returncode != 0:
        print('grib_copy failed with: ', res.stderr)

    res = subprocess.run(['rm', '-f'] + downloaded_gribs)
    if res.returncode != 0:
        print('rm failed with: ', res.stderr)

def clean_output_dir(directory, target):
    to_delete = [f for f  in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if target in to_delete:
        del to_delete[to_delete.index(target)]

    for f in to_delete:
        os.unlink(os.path.join(directory, f))

def load_data(name, output, description = None, clean = False, force_filename = None, **kwargs):
    target = force_filename

    if target is None:
        run, date = get_current_run()
        filename = f'{name}_{date}_{run}.grib2'
        target = os.path.join(output, filename)

        if not os.path.exists(target):
            download_dwd_gribs(date, run, target, output, **kwargs)
        else:
            print(f'{target} already exists. Using the cached version.')

        if clean:
            clean_output_dir(output, filename)

    ds = xr.load_dataset(target, engine='cfgrib')
    if description is not None:
        ds.attrs['_description'] = description
    return ds


debug_config = {
    'output':'dwd_icon-eu',
    'model':'icon-eu',
    'model_long':'icon-eu_europe',
    'clean': True,
    'parameter_caps_in_filename':True,
    'pressure_level_parameters': [
        't',
        'relhum',
        'u',
        'v',
        'fi',
        'clc'
    ],
    'single_level_parameters': [
        'pmsl',
        't_2m',
        'relhum_2m'
    ],
    'pressure_levels':[ 1000, 950, 925, 900, 875, 850, 825, 800, 775, 700, 600, 500, 400, 300, 250, 200, 150, 100 ],
    'steps':[0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48]
}

if __name__ == '__main__':
    load_data('test_icon_eu', **debug_config)

