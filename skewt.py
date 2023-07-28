#!/usr/bin/env python3

# https://unidata.github.io/MetPy/latest/examples/plots/Skew-T_Layout.html#sphx-glr-examples-plots-skew-t-layout-py

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

import csv

import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, Hodograph, SkewT
from metpy.units import units
from metpy.calc import parcel_profile

import datetime
import requests


STATION=10548
DATE=(datetime.date.today() - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
TIME='23:00:00'
# http://weather.uwyo.edu/cgi-bin/bufrraob.py?datetime=2023-07-20%2023:00:00&id=10548&type=TEXT:CSV
URL=f'http://weather.uwyo.edu/cgi-bin/bufrraob.py?datetime={DATE}%20{TIME}&id={STATION}&type=TEXT:CSV'

print(URL)

result = requests.get(URL)
RAW_DATA_LINES=result.content.decode('UTF-8').splitlines()

p = []
T = []
Td = []
wind_speed = []
wind_dir = []

csvreader = csv.reader(RAW_DATA_LINES, dialect='excel')
next(csvreader) # Skip header
for row in csvreader:
    if sum(map(lambda s : len(s.strip()) == 0, row)):
        # skip any line with empty values
        continue

    p.append(float(row[3]))
    T.append(float(row[5]))
    Td.append(float(row[6]))
    wind_speed.append(float(row[12]))
    wind_dir.append(float(row[11]))


p = p * units.hPa
T = T * units.degC
Td = Td * units.degC
wind_speed = wind_speed * units.knots
wind_dir = wind_dir * units.degrees
u, v = mpcalc.wind_components(wind_speed, wind_dir)

ground_parcel = parcel_profile(p, T[0], Td[0])

# Create a new figure. The dimensions here give a good aspect ratio
fig = plt.figure(figsize=(9, 9))

# Grid for plots
gs = gridspec.GridSpec(3, 3)
skew = SkewT(fig, rotation=45, subplot=gs[:, :])

# Plot the data using normal plotting functions, in this case using
# log scaling in Y, as dictated by the typical meteorological plot
skew.plot(p, T, 'r')
skew.plot(p, Td, 'g')
skew.plot(p, ground_parcel, 'b')

barb_div = int(len(p)/20)
skew.plot_barbs(p[::barb_div], u[::barb_div], v[::barb_div])

skew.shade_cape(p,T,ground_parcel)
skew.shade_cin(p,T,ground_parcel)

skew.ax.set_ylim(1000, 100)

# Add the relevant special lines
skew.plot_dry_adiabats()
skew.plot_moist_adiabats()
skew.plot_mixing_lines()

# Good bounds for aspect ratio
skew.ax.set_xlim(-30, 40)

# Create a hodograph
ax = fig.add_subplot(gs[0, -1])
h = Hodograph(ax, component_range=60.)
h.add_grid(increment=20)
h.plot(u[::barb_div], v[::barb_div])

# Show the plot
plt.show()
