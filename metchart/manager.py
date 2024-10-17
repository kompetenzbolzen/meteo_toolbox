from typing import Callable

import yaml
import json
import os

from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool


def run_if_present(key, dct: dict, func: Callable, *args, **kwargs):
    if key in dct:
        func(dct[key], *args, **kwargs)


class Manager:
    def __init__(self, filename: str = 'metchart.yaml'):
        self.aggregators={}
        self._plotters=[]

        self._filename = filename
        self._output_dir = './web/data'
        self._thread_count = max(cpu_count()-1, 1)

        self._load()
        self._parse()

    def run_plotters(self):
        index = ThreadPool(self._thread_count).map(lambda p: p['module'].run(**p['cfg']), self._plotters)

        with open(os.path.join(self._output_dir, 'index.json'), 'w') as f:
            f.write(json.dumps(index, indent=4))

    def _load(self):
        with open(self._filename, 'r') as f:
            self._raw_config = yaml.safe_load(f)

    def _parse(self):
        run_if_present('output', self._raw_config, self._parse_output)
        run_if_present('thread_count', self._raw_config, self._parse_thread_count)
        run_if_present('aggregator', self._raw_config, self._parse_module, self._load_aggregator)
        run_if_present('modifier', self._raw_config, self._parse_module, self._load_modifier)

        run_if_present('plotter', self._raw_config, self._parse_module, self._prepare_plotter)

    def _parse_module(self, data, then: Callable):
        # TODO abstraction prbly off. anonymous reeks
        anonymous = False
        if type(data) is list:
            anonymous = True

        for key in data:
            cfg = data[key] if not anonymous else key

            if 'module' not in cfg:
                print(f'ERROR: {key} is missing the "module" keyword.')
                continue

            classname = cfg['module']
            del cfg['module']
            module = __import__(classname, fromlist=[None])

            then(key if not anonymous else None, module, cfg)

    def _load_aggregator(self, name: str, module, cfg):
        self.aggregators[name] = module.load_data(name=name, **cfg)

    def _load_modifier(self, name: str, module, cfg):
        if 'aggregator' in cfg:
            if type(cfg['aggregator']) == list:
                cfg['data'] = []
                for ag in cfg['aggregator']:
                    cfg['data'].append(self.aggregators[ag])

                del cfg['aggregator']
            else:
                cfg['data'] = self.aggregators[cfg['aggregator']]
                del cfg['aggregator']

        self.aggregators[name] = module.run(**cfg)

    def _prepare_plotter(self, _name, module, cfg):
        if 'aggregator' in cfg:
            cfg['data'] = self.aggregators[cfg['aggregator']]
            del cfg['aggregator']

        self._plotters.append({
                'module': module,
                'cfg': cfg
        })

    def _parse_output(self, data: str):
        self._output_dir = data
    def _parse_thread_count(self, data: int):
        self._thread_count = data
