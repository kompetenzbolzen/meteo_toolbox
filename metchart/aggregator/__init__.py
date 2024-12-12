'''
Aggregator
'''
from enum import StrEnum, auto
import xarray as xr

import os

class AggregatorException(Exception):
    pass

class AggregatorNotImplementedException(AggregatorException):
    pass

class AggregatorDoesNotProvideVariableException(AggregatorException):
    pass

class Variable(StrEnum):
    TEMPERATURE_3D = auto()
    TEMPERATURE_SURFACE = auto()
    HUMIDITY_3D = auto()
    HUMIDITY_SURFACE = auto()
    U_3D = auto()
    V_3D = auto()
    U_SURFACE = auto()
    V_SURFACE = auto()
    GUST_SURFACE = auto()
    PRECIPITATION_ACCUMULATED = auto()


class Dimension(StrEnum):
    LATITUDE = auto()
    LONGITUDE = auto()
    PRESSURE = auto()
    HEIHGT = auto()
    TIME = auto()


class Aggregator():
    PROVIDES=[]

    def __init__(self, cache_dir: os.PathLike):
        self._needed_variables = []
        self._cache_dir = cache_dir
        self._init()

    def load_config(self, *args, **kwargs) -> None:
        self._load_config(*args, **kwargs)

    def add_needed(self, var: Variable) -> None:
        if var not in self.PROVIDES:
            raise AggregatorDoesNotProvideVariableException(f'{var} is not provided')
        if var not in self._needed_variables:
            self._needed_variables.append(var)

    def aggregate(self) -> None:
        self._aggregate()

    def query_data(self, var: Variable, query: list[tuple[Variable,object]]) -> xr.DataArray:
        return self._query_data(var,query)

    def query_dimensions(self, var: Variable):
        return self._query_dimensions(var)

    'Functions  to implement'
    def _init(self):
        pass

    def _load_config(self, *args, **kwargs) -> None:
        raise AggregatorNotImplementedException('_load_config() not implemented')

    def _aggregate(self) -> None:
        raise AggregatorNotImplementedException('_aggregate() not implemented')

    def _query_data(self, var: Variable, query: list[tuple[Variable,object]]) -> xr.DataArray:
        raise AggregatorNotImplementedException('_query_data() not implemented')

    def _query_dimensions(self, var: Variable) -> list[Dimension]:
        raise AggregatorNotImplementedException('_query_dimensions() not implemented')
