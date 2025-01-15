from typing import Callable

import yaml
import json
import os

import importlib

from multiprocessing import cpu_count


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
        for key in self.plotters:
            plt = self.plotters[key]
            plt.plot()

    def aggregate_data(self):
        needed = []
        for key in self.plotters:
            plt = self.plotters[key]
            needed.extend(plt.report_needed_variables())

        for key in self.aggregators:
            agg = self.aggregators[key]
            for n in needed:
                agg.add_needed(n)
            agg.aggregate()

    def _aggregator_callback(self):
        # TODO Implement
        pass

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
            del cfg['module']
            module = importlib.import_module(modname)
            class_obj = getattr(module,classname)

            then(key, class_obj, cfg)

    def _load_aggregator(self, name: str, module, cfg):
        self.aggregators[name] = module(self._cache_dir, name)
        self.aggregators[name].load_config(**cfg)

    def _prepare_plotter(self, name, module, cfg):
        self.plotters[name] = module(self._cache_dir, name, self._aggregator_callback)
        self.plotters[name].load_config(**cfg)

    def _parse_output(self, data: str):
        self._output_dir = data
    def _parse_thread_count(self, data: int):
        self._thread_count = data
