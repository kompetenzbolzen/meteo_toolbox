'''
```yaml
aggregator:
  file:
    module: metchart.aggregator.netcdf.NetCDFAggregator
    files:
      - a.nc
    dimension_map:
      dim_in_file: metchart_dimension
    variable_map:
      var_in_file: metchart_variable
```
'''
from metchart.aggregator import Aggregator, Variable, Dimension
import xarray as xr

import logging
logger = logging.getLogger(__name__)

class NetCDFAggregator(Aggregator):
    def _init(self):
        pass

    def _load_config(self, files: list[str] = [], dimension_map: dict = {}, variable_map: dict = {}) -> None:
        self._files = files

        # NOTE maps are '<original>: <metchart Variable name>'
        self._dim_map = dimension_map
        self._var_map = variable_map

        self._can_provide = [self._var_map[k] for k in self._var_map]
        self._provides_dynamic = [Variable(v) for v in self._can_provide]
        logger.debug(f"Can provide: {self._can_provide}")


    def _aggregate(self) -> None:
        print(self._needed_variables)

        dss = []
        for f in self._files:
            dss.append( xr.open_dataset(f, engine='netcdf4') )

        self._dataset = xr.merge(dss)
        self._dataset = self._dataset.rename_vars(
            { k: Variable(v) for k, v in self._var_map.items() if k in self._dataset and not k == v }
        )
        self._dataset = self._dataset.rename_dims(
            { k: Dimension(v) for k, v in self._dim_map.items() if k in self._dataset and not k == v}
        )

        vars_to_delete = [ v for v in self._dataset.keys() if v not in self._can_provide ]
        dims_to_delete = [
                v for v in self._dataset.dims
                    if v not in self._can_provide
                        and v not in [ self._dim_map[v] for v in self._dim_map ]
        ]

        logger.debug(f'Vars to delete: {vars_to_delete}')
        self._dataset = self._dataset.drop_vars(vars_to_delete)
        logger.debug(f'Dims to delete: {dims_to_delete}')
        self._dataset = self._dataset.drop_dims(dims_to_delete)
