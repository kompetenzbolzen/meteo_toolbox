#!/usr/bin/env python3

import matplotlib.pyplot as plt

import xarray as xr
from metpy.interpolate import cross_section

data = xr.load_dataset('dwd_icon-eu/combined.grib2', engine='cfgrib')
lat, lon = (47.96, 11.99)
data = data.sel(latitude=lat, longitude = lon, method='nearest')
print(data)


# start figure and set axis
fig, ax = plt.subplots(figsize=(5, 5))

#clc = ax.plot(data.step.values.astype('float64'), data.isobaricInhPa, data.ccl.transpose())
clc = ax.imshow(data.ccl.transpose(), extent=(data.step.values.astype(float).min(), data.step.values.astype(float).max(), data.isobaricInhPa.min(), data.isobaricInhPa.max()), aspect='auto', cmap='Blues_r', vmin=0, vmax=100)
plt.colorbar(clc, label='clcov')


cf = ax.contour(data.step.values.astype('float64'), data.isobaricInhPa, data.t.metpy.convert_units('degC').transpose())
ax.clabel(cf, inline=True, fontsize=10)
#plt.colorbar(cf, pad=0, aspect=50)
#plt.colorbar(cf)

barbs = ax.barbs(data.step.values.astype('float64'), data.isobaricInhPa, data.u.transpose(), data.v.transpose())
#ax.barbs(data.u, data.v, color='black', length=5, alpha=0.5)

ax.invert_yaxis()
plt.show()

