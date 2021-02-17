from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("ultimate_cycle.pyx", compiler_directives={'language_level' : "3"}),
    package_dir={'utils': ''},
)