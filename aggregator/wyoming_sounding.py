#!/usr/bin/env python3
import os
import datetime
import requests

import csv

import xarray as xr

import numpy as np

from metpy.units import units
import metpy.calc as mpcalc

import misc

def get_current_run():
    date=(datetime.date.today() - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
    # TODO we also want noon
    hour='23:00:00'
    return (hour, date)

def download_wyoming_csv(station, date, hour, target):
    url=f'http://weather.uwyo.edu/cgi-bin/bufrraob.py?datetime={date}%20{hour}&id={station}&type=TEXT:CSV'
    result = requests.get(url)

    if result.status_code >= 400:
        raise Exception('Failed to Download sounding csv!')

    with open(target, 'w') as f:
        f.write(result.text)

def load_wyoming_csv(filepath, hour, date):
    p = []
    T = []
    Td = []
    wind_speed = []
    wind_dir = []
    r = []

    with open(filepath,'r', newline='') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        for row in reader:
            if sum(map(lambda s : len(s.strip()) == 0, row)):
                # skip any line with empty values
                continue

            if float(row[3]) in p: # Skip double p entries
                continue

            p.append(float(row[3]))
            T.append(float(row[5]))
            Td.append(float(row[6]))
            r.append(float(row[8]))
            wind_speed.append(float(row[12]))
            wind_dir.append(float(row[11]))

    T = T * units.degC
    Td = Td * units.degC
    wind_speed = wind_speed * units.knots
    wind_dir = wind_dir * units.degrees
    u, v = mpcalc.wind_components(wind_speed, wind_dir)

    time = np.datetime64(f'{date}T{hour}')

    # recreate the structure a DWD GRIB produces
    return xr.Dataset(
        {
            "t": (["step", "isobaricInhPa"], [T.to(units.kelvin).magnitude]),
            "td": (["step", "isobaricInhPa"], [Td.to(units.kelvin).magnitude]),
            "r": (["step", "isobaricInhPa"], [r]),
            "u": (["step", "isobaricInhPa"], [u.to('m/s').magnitude]),
            "v": (["step", "isobaricInhPa"], [v.to('m/s').magnitude]),
        },
        coords={
            "isobaricInhPa":  p,
            "step": [np.timedelta64(0, 'ns')],
            "valid_time": (['step'], [time]),
            "time": time,
        },
        attrs={
            "source": "uwyo.edu",
        }
    )

def load_data(name, output, station):
    hour, date = get_current_run()
    misc.create_output_dir(output)

    target = os.path.join(output, f'{name}_{date}_{hour}.csv')

    if not os.path.exists(target):
        download_wyoming_csv(station, date, hour, target)
    else:
        print(f'{target} alreasy exists. Using the cached version.')

    return load_wyoming_csv(target, hour, date)

config_debug = {
    'output': 'wyoming_test',
    'station': '10548'
}

if __name__ == '__main__':
    ds = load_data('test_wyoming_sounding', **config_debug)
    print(ds)
    print(ds.coords['step'])
