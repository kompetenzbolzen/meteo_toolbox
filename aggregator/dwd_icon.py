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

def download_dwd_gribs(config, date, run, target):
    model = config['model']
    model_long = config['model_long']

    misc.create_output_dir(config['output'])

    to_download = []

    for step in config['steps']:
        step_str = f'{step:03d}'

        for parameter in config['pressure_level_parameters']:
            parameter2 = parameter.upper() if config['parameter_caps_in_filename'] else parameter

            for level in config['pressure_levels']:
                filename = f'{model_long}_regular-lat-lon_pressure-level_{date}{run}_{step_str}_{level}_{parameter2}.grib2.bz2'
                URL = f'{BASE}/{model}/grib/{run}/{parameter}/{filename}'

                to_download.append((URL, os.path.join(config['output'], filename)))

        for parameter in config['single_level_parameters']:
            parameter2 = parameter.upper() if config['parameter_caps_in_filename'] else parameter
            filename = f'{model_long}_regular-lat-lon_single-level_{date}{run}_{step_str}_{parameter2}.grib2.bz2'
            URL = f'{BASE}/{model}/grib/{run}/{parameter}/{filename}'

            to_download.append((URL, os.path.join(config['output'], filename)))


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

def load_data(name, config):
    run, date = get_current_run()
    target = os.path.join(config['output'], f'{name}_{date}_{run}.grib2')

    if not os.path.exists(target):
        download_dwd_gribs(config, date, run, target)
    else:
        print(f'{target} alreasy exists. Using the cached version.')

    return xr.load_dataset(target, engine='cfgrib')

config = {
    'output':'dwd_icon-eu',
    'model':'icon-eu',
    'model_long':'icon-eu_europe',
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
    load_data('test_icon_eu', config)
