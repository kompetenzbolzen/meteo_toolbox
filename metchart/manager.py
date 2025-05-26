from typing import Callable

import yaml
import json
import os

import importlib

import functools

from multiprocessing import cpu_count

from metchart.aggregator import DataView

class ManagerException(Exception):
    pass

class ManagerAggregatorNotFoundException(Exception):
    pass

class ManagerPlotterNotFoundException(Exception):
    pass


def run_if_present(key, dct: dict, func: Callable, *args, **kwargs):
    if key in dct:
        func(dct[key], *args, **kwargs)


class Manager:
    def __init__(self, filename: str = 'metchart.yaml'):
        self.aggregators={}
        self.plotters={}

        self._filename = filename
        self._output_dir = './web/data'
        self._thread_count = max(cpu_count()-1, 1)
        self._cache_dir = './metchart_cache'

        self._load()
        self._parse()

    def run_plotters(self):
        index = {}

        for key in self.plotters:
            cfg = self.plotters[key]['config']
            plt = self.plotters[key]['object']

            index[key] = {}

            full_view = DataView(self.aggregators[cfg['aggregator']]._dataset, name=key)

            for query_view in full_view.for_queries(cfg['for_queries'] if 'for_queries' in cfg else []):
                for along_view in query_view.along_dimensions(cfg['along_dimensions'] if 'along_dimensions' in cfg else []):
                    plt.plot(along_view)
                    # TODO we need to handle the index here

    def aggregate_data(self):
        needed = {}

        for key in self.plotters:
            plt = self.plotters[key]['object']
            cfg = self.plotters[key]['config']

            if 'aggregator' not in cfg:
                continue
            agg = cfg['aggregator']
            if agg not in self.aggregators:
                raise ManagerAggregatorNotFoundException(agg)

            if agg not in needed:
                needed[agg] = []

            needed[agg].extend(plt.report_needed_variables())

        for key in self.aggregators:
            agg = self.aggregators[key]
            for n in needed[key]:
                agg.add_needed(n)
            agg.aggregate()

    def _aggregator_callback(self, caller_name: str):
        if caller_name not in self.plotters:
            raise ManagerPlotterNotFoundException(caller_name)

        if 'aggregator' not in self.plotters[caller_name]['config']:
            raise ManagerAggregatorNotFoundException("No aggregator was defined in the config")
        agg = self.plotters[caller_name]['config']['aggregator']

        return self.aggregators[agg].query_data

    def _load(self):
        with open(self._filename, 'r') as f:
            self._raw_config = yaml.safe_load(f)

    def _parse(self):
        run_if_present('output', self._raw_config, self._parse_output)
        run_if_present('thread_count', self._raw_config, self._parse_thread_count)

        run_if_present('aggregator', self._raw_config, self._parse_module, self._load_aggregator)
        # TODO reactivate
        #run_if_present('modifier', self._raw_config, self._parse_module, self._load_modifier)

        run_if_present('plotter', self._raw_config, self._parse_module, self._prepare_plotter)

    def _parse_module(self, data: dict, then: Callable):
        for key in data:
            cfg = data[key]

            if 'module' not in cfg:
                print(f'ERROR: {key} is missing the "module" keyword.')
                continue

            modname, classname = cfg['module'].rsplit('.',1)
            module = importlib.import_module(modname)
            class_obj = getattr(module,classname)

            then(key, class_obj, cfg)

    def _load_aggregator(self, name: str, module, cfg: dict):
        # TODO feels a bit hacky
        if 'module' in cfg:
            del cfg['module']

        self.aggregators[name] = module(self._cache_dir, name)
        self.aggregators[name].load_config(**cfg)

    def _prepare_plotter(self, name, module, cfg):
        self.plotters[name] = {
                "object" : module(
                    self._cache_dir, name,
                    functools.partial(self._aggregator_callback, name) ),
                "config" : cfg
            }

        if 'config' not in cfg:
            cfg['config'] = {}

        self.plotters[name]['object'].load_config(**cfg['config'])

    def _parse_output(self, data: str):
        self._output_dir = data
    def _parse_thread_count(self, data: int):
        self._thread_count = data
