#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

import xarray as xr
from metpy.interpolate import cross_section

clcov_cmap = {
    'red': (
        (0.0, 0.0, 0.0),
        (0.1, 1.0, 1.0),
        (1.0, 0.2, 0.2),
    ),
    'green': (
        (0.0, 0.0, 0.0),
        (0.1, 1.0, 1.0),
        (1.0, 0.2, 0.2),
    ),
    'blue': (
        (0.0, 1.0, 1.0),
        (0.1, 1.0, 1.0),
        (1.0, 0.2, 0.2),
    ),
}

mpl.colormaps.register(LinearSegmentedColormap('clcov', clcov_cmap))

data = xr.load_dataset('dwd_icon-eu/combined.grib2', engine='cfgrib')
lat, lon = (47.96, 11.99)
data = data.sel(latitude=lat, longitude = lon, method='nearest')
print(data)


# start figure and set axis
fig, ax = plt.subplots(figsize=(5, 5))

ax.set_ylabel('Pressure level [hPa]')

#clc = ax.plot(data.step.values.astype('float64'), data.isobaricInhPa, data.ccl.transpose())
#clc = ax.imshow(data.ccl.transpose(), extent=(data.step.values.astype(float).min(), data.step.values.astype(float).max(), data.isobaricInhPa.min(), data.isobaricInhPa.max()), aspect='auto', cmap='Blues_r', vmin=0, vmax=100)
#plt.colorbar(clc, label='clcov')
# Blues_r
clc = ax.contourf(data.step.values.astype('float64'), data.isobaricInhPa, data.ccl.transpose(), cmap='clcov', vmin=0, vmax=100, levels=9)

# use Format parameter for n/8
plt.colorbar(clc, label='cloudcov', extendfrac=None, ticks=[100*n/8 for n in range(9)], format=lambda x,_: f'{int(x/12.5)}/8')


cf = ax.contour(data.step.values.astype('float64'), data.isobaricInhPa, data.t.metpy.convert_units('degC').transpose())
ax.clabel(cf, inline=True, fontsize=10)
#plt.colorbar(cf, pad=0, aspect=50)
#plt.colorbar(cf)

barbs = ax.barbs(data.step.values.astype('float64'), data.isobaricInhPa, data.u.transpose(), data.v.transpose())
#ax.barbs(data.u, data.v, color='black', length=5, alpha=0.5)

ax.invert_yaxis()
plt.show()

