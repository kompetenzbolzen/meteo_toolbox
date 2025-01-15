'''
Plotter base class
'''

from collections.abc import Callable
from ..aggregator import Variable

class PlotterException(Exception):
    pass

class PlotterNotImplementedException(PlotterException):
    pass

class Plotter:
    def __init__(self, cache_dir : str, name : str, aggregator_callback : Callable):
        self._name = name
        self._aggregator_callback = aggregator_callback
        # TODO typehint for path
        self._cache_dir = cache_dir

    def load_config(self, *args, **kwargs) -> None:
        self._load_config(*args, **kwargs)

    # TODO we could maybe do this in load_config?
    def report_needed_variables(self) -> list[Variable]:
        return self._report_needed_variables()

    def plot(self):
        return self._plot()

    'to implement'
    def _load_config(self, *args, **kwargs) -> None:
        raise PlotterNotImplementedException('_load_config()')

    def _report_needed_variables(self) -> list[Variable]:
        raise PlotterNotImplementedException('_report_needed_variables()')

    def _plot(self) -> None:
        raise PlotterNotImplementedException('_plot()')

class DebugPlotter(Plotter):
    def _load_config(self):
        pass

    def _report_needed_variables(self) -> list[Variable]:
        return [Variable.U_SURFACE, Variable.V_SURFACE]

    def _plot(self):
        print("I am plotting")
