'''
Aggregator
'''
from __future__ import annotations

from enum import StrEnum, auto
from typing import Iterable
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
    SNOW_DEPTH = auto()
    CLOUDCOVER_3D = auto()
    CONVECTION_WET_BASE = auto()
    CONVECTION_WET_TOP = auto()
    CONVECTION_DRY_TOP = auto()
    PRESSURE_SEA_LEVEL = auto()


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

    # NOTE Deprecated
    def _query_data(self, var: Variable, query: list[tuple[Variable,object]]) -> xr.DataArray:
        raise AggregatorNotImplementedException('_query_data() not implemented')

    def _query_dimensions(self, var: Variable) -> list[Dimension]:
        raise AggregatorNotImplementedException('_query_dimensions() not implemented')


class DataView():
    def __init__(self, dataset: xr.Dataset,
                 query: dict | None = None,
                 name: str | None = None,
                 long_name: str | None = None):
        self._dataset = dataset
        self.query = query
        self.name = name
        self.long_name = long_name

    def get(self) -> xr.Dataset:
        if self.query is not None:
            return self._dataset.sel(** self.query)
        return self._dataset

    def for_queries(self, queries: list[dict]) -> Iterable[DataView]:
        if len(queries) < 1:
            yield self

        for query in queries:
            yield DataView(self.get(), **query)

    def along_dimensions(self, dimensions: list[Dimension]) -> Iterable[DataView]:
        if len(dimensions) < 1:
            yield self

        for query_parts in itertools.product(*[
                                        [{d:s} for s in self._dataset[d].values]
                                        for d in dimensions
                                     ]):
            query = {}
            for p in query_parts:
                query.update(p)
            # NOTE we keep name and long_name along dimensions (for grouping outputs)
            yield DataView(self.get(), query=query,
                           name=self.name, long_name=self.long_name)

    # TODO add get min and max of whole dataset here
    # this would make min_max easier
