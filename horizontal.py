#!/usr/bin/env python3
import xarray as xr

from metpy.plots import MapPanel, PanelContainer, RasterPlot, ContourPlot

config = {
    'source': 'dwd_icon-d2/combined.grib2',
    'plots': [
        {
            'name':'',
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

def run(config):
    data = xr.load_dataset(config['source'], engine='cfgrib')

    for plot in config['plots']:
        _plot(data, **plot)

def _plot(data, name, area, layers):

    for step in data.coords['step']:
        this_step = data.sel(step=step)

        map_layers = []

        for layer in layers:
            map_layers.append(_layer(this_step, **layer))

        panel = MapPanel()
        #panel.area = 'de'
        panel.projection = 'mer'
        panel.layers = ['coastline', 'borders']
        panel.plots = map_layers

        pc = PanelContainer()
        pc.size = (8, 8)
        pc.panels = [panel]
        pc.draw()
        pc.show()

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
    run(config)
