'''
Plotter base class
'''

from ..aggregator import Variable

class PlotterException(Exception):
    pass

class PlotterNotImplementedException(PlotterException):
    pass

class Plotter:
    def __init__(self):
        pass

    def load_config(self, *args, **kwargs) -> None:
        self._load_config(*args, **kwargs)

    # TODO we could maybe do this in load_config?
    def report_needed_variables(self) -> list[Variable]:
        return self._report_needed_variables()

    def plot(self):
        return self._plot()

    'to implement'
    def _load_config(self, *args, **kwargs):
        raise PlotterNotImplementedException('_load_config()')

    def _report_needed_variables(self) -> list[Variable]:
        raise PlotterNotImplementedException('_report_needed_variables()')

    def _plot(self):
        raise PlotterNotImplementedException('_plot()')
