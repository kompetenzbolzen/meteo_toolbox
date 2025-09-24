from . import Plotter
from ..aggregator import DataView, Variable

class Debug (Plotter):
    def _init(self):
        pass

    def _load_config(self):
        pass

    def _report_needed_variables(self) -> list[Variable]:
        return []

    def _plot(self, view: DataView, filename_prefix: str):
        print(view.get())
