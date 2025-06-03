from IPython import embed, start_ipython
from .manager import Manager
from importlib import reload as import_reload

from traitlets import config



def _set_globals():
    #globals()["Manager"] = metchart.manager.Manager
    pass

def reload():
    import_reload(globals()['metchart'])
    _set_globals()

def test_load():
    m = Manager("examples/refactor.yaml")
    m.aggregate_data()
    for a in m.aggregators:
        print(m.aggregators[a]._dataset)


def main():
    #from traitlets.config import Config
    #c = Config()
    #import metchart

    #c.InteractiveShellApp.exec_lines = [
    #        '%load_ext autoreload',
    #        '%autoreload 2'
    #]
    #start_ipython(argv=[], user_ns=locals(), user_global_s=globals(), config=c)
    embed(header="""
    metchart Interacte debug shell

    Manager("path/to/config.yaml")
    """, colors="neutral")
