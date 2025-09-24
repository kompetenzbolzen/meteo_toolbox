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


class Index:
    '''
    Very hacky class to simulate behaviour of old index
    to finally deploy new format to prod
    '''
    def __init__(self, output_dir: str):
        self._output_dir = output_dir

        self._sub_indices = {}
        self._sub_type    = {}


    def add_object(self, filename: str, view_chain):
        sub_name = '_'.join([a['name'] for a in view_chain[:-1]])
        last_chain = len(view_chain) -1

        display_name = ""
        list_title = ""
        if 'name' in view_chain[last_chain]:
            display_name = view_chain[last_chain]['name']
            list_title = "Location"
        elif 'query' in view_chain[last_chain] and 'time' in view_chain[last_chain]['query']:
            display_name = view_chain[last_chain]['query']['time']
            list_title = "Time"
        else:
            print('what?')
            print(view_chain)

        if sub_name not in self._sub_indices:
            self._sub_indices[sub_name] = []
            self._sub_type[sub_name] = list_title

        self._sub_indices[sub_name].append({'file': filename, 'display_name': display_name})

    def save(self):
        index = [{ 'name': sub,
                   'indexfile': f'{sub}.index.json',
                   'list_title': self._sub_type[sub] }
                for sub in self._sub_indices ]

        with open(f'{self._output_dir}/index.json','w') as f:
            f.write(json.dumps(index, indent=4))

        for sub in self._sub_indices:
            with open(f'{self._output_dir}/{sub}.index.json','w') as f:
                f.write(json.dumps(self._sub_indices[sub], indent=4))


class Manager:
    def __init__(self, filename: str = 'metchart.yaml'):
        self.aggregators={}
        self.plotters={}

        self._filename = filename
        self._output_dir = './metchar_output'
        self._thread_count = max(cpu_count()-1, 1)
        self._cache_dir = './metchart_cache'

        self._load()
        self._parse()

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)

    def run_plotters(self):
        index = Index(self._output_dir)

        for key in self.plotters:
            cfg = self.plotters[key]['config']
            plt = self.plotters[key]['object']

            full_view = DataView(self.aggregators[cfg['aggregator']]._dataset, name=key)

            for query_view in full_view.for_queries(cfg['for_queries'] if 'for_queries' in cfg else []):
                for along_view in query_view.along_dimensions(cfg['along_dimensions'] if 'along_dimensions' in cfg else []):
                    real_filename = plt.plot(along_view, along_view.generate_unique_name() )

                    index.add_object(real_filename, along_view.generate_chain())

        index.save()


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
                    self._cache_dir, self._output_dir, name,
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
