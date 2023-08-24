import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, Hodograph, SkewT
from metpy.units import units

class Skewt:
    def __init__(self, p, T, Td, title=None):
        self._p = p
        self._T = T
        self._Td = Td


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
        self._skew.plot_barbs(self._p, u, v)

    def addInfo(self, lines):
        # TODO
        ax = self._fig.add_subplot(self._gs[1,-1])
        ax.text(0, 0, lines, ha='left', va='center', size=12)
        ax.axis("off")


    def plot(self, filename=None):
        # Add the relevant special lines
        #self._skew.ax.set_ylim(max(self._p), min(self._p))
        self._skew.ax.set_ylim(1000, 100)
        self._skew.plot_dry_adiabats()
        self._skew.plot_moist_adiabats()
        self._skew.plot_mixing_lines()

        # Good bounds for aspect ratio
        self._skew.ax.set_xlim(-30, 40)

        if filename is not None:
            plt.savefig(filename)
        else:
            plt.show()
