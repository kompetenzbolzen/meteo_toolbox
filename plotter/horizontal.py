#!/usr/bin/env python3
import os
import json

import xarray as xr

import numpy as np
from metpy.plots import MapPanel, PanelContainer, RasterPlot, ContourPlot

import misc

config = {
    'source': 'dwd_icon-eu/combined.grib2',
    'plots': [
        {
            'name':'r_t-750',
            'area': None,
            'layers': [
                {
                    'layertype': 'raster',
                    'field': 'r',
                    'level': 750,
                },
                {
                    'layertype': 'contour',
                    'field': 't',
                    'level': 750,
                    'contours': 5,
                    'clabels': True
                },
            ]
        },
    ]
}

def run(data, plots, output='.'):
    misc.create_output_dir(output)
    index = []

    for plot in plots:
        index.append(_plot(data, output, **plot))

    return index

def _plot(data, output, name, layers, area = None):
    index = []

    for step in data.coords['step']:
        this_step = data.sel(step=step)

        map_layers = []

        for layer in layers:
            map_layers.append(_layer(this_step, **layer))

        valid = misc.np_time_convert(step.valid_time.values)
        init = misc.np_time_convert(step.time.values)

        valid_str = valid.strftime('%d %b %Y - %HUTC')
        init_str = init.strftime('%d %b %Y - %HUTC')
        hours_since_init_str = str(int(this_step.step.values / np.timedelta64(1,'h'))).zfill(2)
        init_for_filename = init.strftime('%Y-%m-%d-%HUTC')

        panel = MapPanel()
        if area is not None:
            panel.area = area
        panel.projection = 'mer'
        panel.layers = ['coastline', 'borders']
        panel.plots = map_layers
        panel.left_title = f'{name} VALID: {valid_str} (INIT +{hours_since_init_str}) INIT: {init_str}'
        panel.right_title = 'FORECAST DWD ICON-EU'

        pc = PanelContainer()
        pc.size = (12.8, 9.6)
        pc.panels = [panel]
        pc.draw()
        #pc.show()
        outname = f'{name}_{init_for_filename}+{hours_since_init_str}.png'
        pc.save(os.path.join(output, outname))

        index.append(
            {
                'file': outname,
                'init': init_str,
                'valid': valid_str,
                'valid_offset': hours_since_init_str
            }
        )

    with open(os.path.join(output, f'{name}.index.json'), 'w') as f:
        f.write(json.dumps(index, indent=4))

    return { 'name': name, 'indexfile': f'{name}.index.json' }

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
        }
    }

    args = layertypes[layertype]['defaults'] | kwargs

    ret = layertypes[layertype]['obj'](**args)
    ret.data = data

    return ret

if __name__ == '__main__':
    run(**config)
