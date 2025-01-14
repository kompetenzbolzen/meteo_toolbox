from IPython import embed
from .manager import Manager

def main():
    embed(header="""
    metchart Interacte debug shell

    Manager("path/to/config.yaml")
""", colors="neutral")
