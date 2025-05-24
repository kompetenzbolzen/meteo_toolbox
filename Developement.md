# mtechart Module API

`metchart` uses pluggable modules.

## Aggregator

An aggregator is responsible for acquiring data.
The data is exposed as an `xarray.Dataset`.

### Configuration

An aggregator is defined in the `aggregator` section of the config file.
`module` sets the Class to be instanciated for this aggregator.
All further key/value pairs are passed verbatim to the aggregator as configuration.

```yaml
aggregator:
  <name>:
    module: python.module.path.Aggregator
    <key>: <value>
```

### Implementation

```python
from metchart.aggregator import Aggregator, Variable
import xarray as xr

class MyAggregator(Aggregator):
    PROVIDES=[
        Variable.U_3D,
	Variable.V_3D,
    ]

    def _init(self):
        pass

    def _load_config(self, config_key_1, config_key_2) -> None:
        self._config_key_1 = config_key_1
        self._config_key_2 = config_key_2

    def _aggregate(self) -> None:
        print(self._needed_variables)
	self._dataset = xr.Dataset()
```

## Plotter

Plotters consume data from an aggregator and produce a product.

### Configuration

A plotter is defined in the `plotter` section of the config file.
`module` sets the Class to be instanciated for this plotter.
`aggregator` specifies the aggregator to use as the data source.

It is often needed to create similar products for different parts of a dataset, e.g. different locations,
or to repeat it along a dimension, e.g. time.
`along_dimension` is a list of dimensions.
The plot is repeated for the cartesian product for all values of the given dimensions.
`for_queries` specifies a list of queries for which the plot and the product of `along_dimension` is repeated.
the values of the `query` field is passed verbatim to `xarray.Dataset.sel()`.

```yaml
plotter:
  <name>:
    module: python.module.path.Plotter
    aggregator: <aggregator name>
    config:
      <key>: <value>
    for_queries:
      - name: <query_name>
        long_name: <descriptive query name>
        query:
          <variable>: <value>
          ..
    along_dimension:
      - <dimension>
```

### Implementation

```python
from metchart.plotter import Plotter
from metchart.aggregator import Variable

class DebugPlotter(Plotter):
    def _load_config(self, **kwargs):
        print(kwargs)
        self._cfg = kwargs

    def _report_needed_variables(self) -> list[Variable]:
        return [Variable.U_SURFACE, Variable.V_SURFACE]

    def _plot(self, view):
        print(view)
```
