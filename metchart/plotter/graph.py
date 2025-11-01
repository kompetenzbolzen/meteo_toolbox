from metchart.plotter import Plotter
from metchart.aggregator import Variable, Dimension

import matplotlib.pyplot as plt

import os

import logging
logger = logging.getLogger(__name__)

class GraphPlotter(Plotter):
    def _load_config(self, x_dim: str|None = None, vars: list[str]|dict = []):
        self._x_dim = Dimension(x_dim)
        self._vars = [Variable(v) for v in vars]

        self._vars_args = {}
        self._vars_have_args = False

        # TODO this is hella ugly. we can prbly do without any diverging logic paths
        if type(vars) is dict:
            self._vars_args = { Variable(k): vars[k] for k in vars }
            self._vars_have_args = True

    def _report_needed_variables(self) -> list[Variable]:
        return self._vars

    def _plot(self, view, filename_prefix: str) -> str:
        ds = view.get()

        fig = plt.figure()
        ax = fig.add_subplot()

        if self._x_dim is not None:
            ax.set_xlabel(self._x_dim)
        for v in self._vars:
            args = self._vars_args[v] if self._vars_have_args else {}
            # WARN this could bite my ass if x_dim has no matching variable
            ax.plot(ds[self._x_dim], ds[v], **args)

        plt.savefig(os.path.join(self._output_dir, f'{filename_prefix}.png'))

        return f'{filename_prefix}.png'
