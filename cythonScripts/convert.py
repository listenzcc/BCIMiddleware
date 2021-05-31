'''
FileName: convert.py
Author: Chuncheng
Version: V0.0
Purpose: Convert the .py Files into its Compiled Version
'''

from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules=cythonize(["BCIDecoder.py"]))
