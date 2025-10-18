import os
import datetime
import requests

import csv

import xarray as xr

import numpy as np

from metpy.units import units
import metpy.calc as mpcalc

from .. import misc

from ..aggregator import Aggregator, Variable, Dimension

class IconAggregator(Aggregator):
    PROVIDES = [
            Variable.TEMPERATURE_3D,
            Variable.HUMIDITY_3D,
            Variable.U_3D,
            Variable.V_3D,
    ]
    def _init(self):
        self._dataset = None
        self._hour = None
        self._date = None
        self._stations = []

    def _load_config(self, stations: list[int]) -> None:
        self._hour, self._date = get_current_run()
        self._stations = stations

    def _aggregate(self) -> None:
        dss = []
        for station in self._stations:
            target = os.path.join(self._cache_dir, f'{station}_{self._date}_{self._hour}.csv')

            download_wyoming_csv(station, self._date, self._hour, target)
            dss.append(load_wyoming_csv(target, self._hour, self._date, station))
        self._dataset = xr.concat(dss, dim=Dimension.STATION)

def get_current_run():
    date=(datetime.date.today() - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
    # TODO we also want noon
    hour='23:00:00'
    return (hour, date)

def download_wyoming_csv(station, date, hour, target):
    url=f'http://weather.uwyo.edu/cgi-bin/bufrraob.py?datetime={date}%20{hour}&id={station}&type=TEXT:CSV'
    result = requests.get(url)

    if result.status_code >= 400:
        # TODO Error handling
        raise Exception('Failed to Download sounding csv!')

    with open(target, 'w') as f:
        f.write(result.text)

def load_wyoming_csv(filepath, hour, date, station):
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

    return xr.Dataset(
        {
            #"td": ([Dimension.TIME, Dimension.PRESSURE], [Td.to(units.kelvin).magnitude]),
            Variable.TEMPERATURE_3D:
                ([Dimension.TIME, Dimension.PRESSURE], [T.to(units.kelvin).magnitude]),
            Variable.HUMIDITY_3D:
                ([Dimension.TIME, Dimension.PRESSURE], [r]),
            Variable.U_3D:
                ([Dimension.TIME, Dimension.PRESSURE], [u.to('m/s').magnitude]),
            Variable.V_3D:
                ([Dimension.TIME, Dimension.PRESSURE], [v.to('m/s').magnitude]),
        },
        coords={
            Dimension.PRESSURE:  p,
            Dimension.TIME: Dimension.TIME,
            Dimension.INIT_TIME: time,
            Dimension.STATION: station
        },
        attrs={
            "source": "uwyo.edu",
        }
    )
