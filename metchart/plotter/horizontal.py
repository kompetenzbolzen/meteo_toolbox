#!/usr/bin/env python3
import os
import json

import xarray as xr

import numpy as np
import matplotlib.pyplot as plt
from metpy.plots import MapPanel, PanelContainer, RasterPlot, ContourPlot, BarbPlot

from .. import misc

from . import Plotter
from ..aggregator import DataView, Variable

'''
plotter:
  horizontal:
    module: metchart.plotter.horizontal.HorizontalPlotter
    aggregator: icon_eu
    config:
      layers:
        - layertype: raster
          field: u_surface
    along_dimensions:
      - time
'''

class HorizontalPlotter (Plotter):
    def _init(self):
        self._plot_configs = {}

    def _load_config(self, layers: list):
        self._layer_configs = layers

    def _report_needed_variables(self) -> list[Variable]:
        ret = []
        for layer in self._layer_configs:
            field = layer['field'].lower()
            ret.append(Variable(field))
        return ret

    def _plot(self, view: DataView):
        #ds = self._aggregator_callback()._dataset
        print("I am plotting")
        _plot(view.get(), self._cache_dir, view.name, self._layer_configs)

def _plot(data, output, name, layers, area = None):
    index = []

    this_step = data

    map_layers = []

    for layer in layers:
        map_layers.append(_layer(this_step, **layer))

    valid = misc.np_time_convert(data.time.values)
    init = misc.np_time_convert(data.init_time.values)

    valid_str = valid.strftime('%d %b %Y - %HUTC')
    init_str = init.strftime('%d %b %Y - %HUTC')
    hours_since_init_str = str(int((valid - init) / np.timedelta64(1,'h'))).zfill(2)
    init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

    panel = MapPanel()
    if area is not None:
        panel.area = area
    panel.projection = 'mer'
    panel.layers = ['coastline', 'borders']
    panel.plots = map_layers
    panel.left_title = f'{name} VALID: {valid_str} (INIT +{hours_since_init_str}) INIT: {init_str}'
    if '_description' in data.attrs:
        panel.right_title = data.attrs['_description']

    pc = PanelContainer()
    pc.size = (12.8, 9.6)
    #pc.figure.layout='constrained'
    pc.panels = [panel]
    pc.draw()
    #pc.show()
    outname = f'{name}_{init_for_filename}+{hours_since_init_str}.png'
    pc.save(os.path.join(output, outname))
    plt.close('all')

    print("save to", outname)

    index.append(
        {
            'file': outname,
            'init': init_str,
            'valid': valid_str,
            'valid_offset': hours_since_init_str,
            'display_name': hours_since_init_str,
            'id': name
        }
    )

    #with open(os.path.join(output, f'{name}.index.json'), 'w') as f:
    #    f.write(json.dumps(index, indent=4))

    #return { 'name': name, 'indexfile': f'{name}.index.json', 'list_title': 'INIT+' }

def _layer(data, layertype, **kwargs):
    layertypes={
        'raster': {
            'obj': RasterPlot,
            'defaults': {
                'colorbar': 'vertical',
            }
        },
        'contour': {
            'obj': ContourPlot,
            'defaults': {}
        },
        'barbs': {
            'obj': BarbPlot,
            'defaults': {}
        }
    }

    args = layertypes[layertype]['defaults'] | kwargs

    ret = layertypes[layertype]['obj'](**args)
    ret.data = data

    return ret
