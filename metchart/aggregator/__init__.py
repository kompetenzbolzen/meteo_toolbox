'''
Aggregator
'''
from __future__ import annotations

from enum import StrEnum, auto
import xarray as xr

import itertools

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
    HEIGHT = auto()
    TIME = auto()
    INIT_TIME = auto()

class Aggregator():
    PROVIDES=[]

    def __init__(self, cache_dir: os.PathLike, name: str):
        self._needed_variables = []
        self._cache_dir = cache_dir
        self._name = name
        # WARNING This is hacky. we need a clear interface for directly accessing the dataset
        self._dataset = None
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

    'Functions to implement'
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


class DataView():
    def __init__(self, aggregator: Aggregator,
                 query: dict | None = None,
                 name: str | None = None,
                 long_name: str | None = None):
        self._aggregator = aggregator
        self.query = query
        self.name = name
        self.long_name = long_name

    def get(self) -> xr.Dataset:
        raise AggregatorNotImplementedException('get not implemented')

    # TODO remove
    @staticmethod
    def along_dimensions(source: Aggregator | DataView, dimensions: list[Dimension]) -> list[DataView]:
        raise AggregatorNotImplementedException('along_dimensions not implemented')

    # TODO remove
    @staticmethod
    def for_queries(source: Aggregator | DataView, queries: list[dict]) -> list[DataView]:
        raise AggregatorNotImplementedException('for_queries not implemented')

class DataViewIterator():
    def __init__(self, aggregator: Aggregator,
                 along_dimensions: list[Dimension]  = [],
                 for_queries: list[dict] = []):
        self._queries = for_queries
        self._along_dimensions = along_dimensions
        self._aggregator = aggregator

        self._counter = 0

        if len(self._queries) == 0:
            self._queries = [{'query':{}}]

        query_product = itertools.product(*[
            [{d:s} for s in self._aggregator._dataset[d]]
            for d in self._along_dimensions
        ])

        # TODO another cartesian Product should live here


    def __iter__(self):
        return self

    def __next__(self):
        pass
