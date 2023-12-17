# meteo toolbox

This projects aims to provide a declarative frontend to create weather charts from a variety of sources.
It mainly builds upon [MetPy](https://unidata.github.io/MetPy/latest/index.html),
[Xarray](https://docs.xarray.dev) and [cfgrib](https://github.com/ecmwf/cfgrib).

## Requirements

This project depends on the [ecCodes](https://confluence.ecmwf.int/display/ECC/ecCodes+Home) tools,
as well as some Python libraries.

The former can be installed with `pip install -r requirements.txt`.

*ecCodes* is available in the [Arch User Repository](https://aur.archlinux.org/packages/eccodes).

## Usage

A configuration file is needed to run.
It defines datasources, as well as plots to create.

See the included `config.yaml` for an example configuration.

To trigger chart generation, execute `run.py`.
If no path is provided as argument, `config.yaml` is used by default.

## Data Sources

Currently, *DWD* models *ICON*, *ICON-EU* and *ICON-D2* fom [DWD OpenData site](https://opendata.dwd.de/weather/nwp/)
and Sounding Data from the *University of Wyoming* [Atmospheric Science Radiosonde Archive](http://weather.uwyo.edu/upperair/bufrraob.shtml)
are supported.
I plan to extend that to at least [ECMWF OpenData](https://www.ecmwf.int/en/forecasts/datasets/open-data).

It is my goal to make every plotter work with as many data sources as possible,
to enable the parallel usage of as many datasources as possible.

## Web

`web/` is a **very** basic web frontend for the generated plots.
If all the data is put in `web/data/` (which is the default),
it can be started by just running `python -m http.server -d web/`.

Next to the plots, each plotter also creates an `index.NAME.json`,
which the webpage uses to list products.

## License

This project is licensed under the *MIT Licese*. See [LICENSE](LICENSE) for details.
