import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

import numpy as np

import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, Hodograph, SkewT
from metpy.units import units

class Skewt:
    def __init__(self, p, T, Td, max_barbs=20, title=None):
        self._p = p
        self._T = T
        self._Td = Td

        self._info_lines = []

        self.barb_div = int(max(len(p)/max_barbs,1))


        # Create a new figure. The dimensions here give a good aspect ratio
        self._fig = plt.figure(figsize=(9, 9))
        plt.rcParams["font.family"] = "monospace"
        #self._fig = plt.figure()

        if title is not None:
            plt.suptitle(title, x=0, y=0, va='bottom', ha='left')

        # Grid for plots
        self._gs = gridspec.GridSpec(3, 3)
        self._skew = SkewT(self._fig, rotation=45, subplot=self._gs[:, :2])

        # Plot the data using normal plotting functions, in this case using
        # log scaling in Y, as dictated by the typical meteorological plot
        self._skew.plot(p, T, 'r')
        self._skew.plot(p, Td, 'b')

        plt.xlabel('$T$ $[^o C]$')
        plt.ylabel('$p$ $[hPa]$')

    def addWindUV(self, u, v):
        self._u = u
        self._v = v

        ax = self._fig.add_subplot(self._gs[0, -1])
        h = Hodograph(ax, component_range=max(u + v).magnitude)
        h.add_grid(increment=20)
        h.plot_colormapped(u, v, self._p)
        plt.tight_layout()
        plt.xlabel('$m/s$')
        plt.ylabel('$m/s$')

        self._skew.plot_barbs(self._p[::self.barb_div], u[::self.barb_div], v[::self.barb_div])

    def addInfo(self, line):
        self._info_lines.append(line)

    def addAnalysis(self, analysis='ccl', shade=False):
        f = {'ccl': self._cclAnalysis, 'lcl': self._lclAnalysis}

        lvl, parcel = f[analysis]()

        self._skew.plot(self._p, parcel, 'y')
        self._skew.plot(lvl[0], lvl[1], 'o', markerfacecolor='red', linewidth=1)

        # TODO why exception on cape_cin()?
        # ValueError: zero-size array to reduction operation minimum which has no identity
        # https://github.com/Unidata/MetPy/pull/3132
        try:
            cape, cin = mpcalc.cape_cin(self._p, self._T, self._Td, parcel, which_el='top')
            self.addInfo(f'CAPE {int(cape.magnitude)} $J/kg$ CIN {int(cin.magnitude)} $J/kg$')
        except ValueError:
            print('CAPE/CIN Failed with ValueError')
            self.addInfo('CAPE #### CIN ####')

        if shade:
            self._skew.shade_cape(self._p,self._T,parcel)
            self._skew.shade_cin(self._p,self._T,parcel)

    def _cclAnalysis(self):
        #p = np.arange(max(self._p).magnitude, min(self._p).magnitude, -50) * units.hPa

        ccl = mpcalc.ccl(self._p,self._T,self._Td)
        ccl_ground=mpcalc.dry_lapse(self._p[:1], ccl[1], ccl[0])
        ccl_ground_parcel= mpcalc.parcel_profile(self._p, ccl_ground[0], self._Td[0])

        return (ccl, ccl_ground_parcel)

    def _lclAnalysis(self):
        ground_parcel= mpcalc.parcel_profile(self._p, self._T[0], self._Td[0])
        lcl = mpcalc.lcl(self._p[0],self._T[0],self._Td[0])

        return (lcl, ground_parcel)

    def _buildInfoBox(self):
        ax = self._fig.add_subplot(self._gs[1,-1])
        ax.text(0, 0, '\n'.join(self._info_lines), ha='left', va='center',
                size=10, fontfamily='monospace')
        ax.axis("off")

    def plot(self, filename=None):
        self._buildInfoBox()

        # Add the relevant special lines
        #self._skew.ax.set_ylim(max(self._p), min(self._p))
        self._skew.ax.set_ylim(1000, 100)
        self._skew.plot_dry_adiabats(linewidth=1)
        self._skew.plot_moist_adiabats(linewidth=1)
        self._skew.plot_mixing_lines(linewidth=1)

        # Good bounds for aspect ratio
        self._skew.ax.set_xlim(-30, 40)

        if filename is not None:
            plt.savefig(filename)
        else:
            plt.show()
