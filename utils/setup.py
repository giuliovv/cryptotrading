from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("ultimate_cycle.pyx"),
    package_dir={'utils': ''},
)