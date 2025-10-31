'''
Plotter base class
'''
import logging
logger = logging.getLogger(__name__)

from collections.abc import Callable
from ..aggregator import Variable, DataView

class PlotterException(Exception):
    pass

class PlotterNotImplementedException(PlotterException):
    pass

class Plotter:
    def __init__(self, cache_dir : str, output_dir: str, name : str, aggregator_callback : Callable):
        self._name = name
        self._aggregator_callback = aggregator_callback
        # TODO typehint for path
        self._cache_dir = cache_dir
        self._output_dir = output_dir
        self._init()
        logger.debug(f"{self._name}: init")

    def load_config(self, *args, **kwargs) -> None:
        self._load_config(*args, **kwargs)
        logger.debug(f"{self._name}: config loaded")

    # TODO we could maybe do this in load_config?
    def report_needed_variables(self) -> list[Variable]:
        logger.debug(f"{self._name}: collecting needed variables")
        return self._report_needed_variables()

    def plot(self, view: DataView, filename_prefix: str) -> str:
        logger.debug(f"{self._name}: plotting")
        return self._plot(view, filename_prefix)

    def _init(self):
        pass

    'to implement'
    def _load_config(self, *args, **kwargs) -> None:
        raise PlotterNotImplementedException('_load_config()')

    def _report_needed_variables(self) -> list[Variable]:
        raise PlotterNotImplementedException('_report_needed_variables()')

    def _plot(self, view: DataView, filename_prefix: str) -> str:
        '''
        _plot has to return the filename of produced filename relative to self._output_dir
        '''
        raise PlotterNotImplementedException('_plot()')

class DebugPlotter(Plotter):
    def _load_config(self, **kwargs):
        self._cfg = kwargs

    def _report_needed_variables(self) -> list[Variable]:
        return []

    def _plot(self, view, filename_prefix: str) -> str:
        print(view.get())
        return ''
