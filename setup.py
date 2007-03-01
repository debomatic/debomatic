#!/usr/bin/env python

# Written by Luca Falavigna
# (C) 2007, Luca Falavigna

from distutils.core import setup, Extension
   
debomaticmodule = Extension('debomatic', sources = ['debomaticmodule.c'])

setup(name='debomatic', version="0.1",
      description = 'Automatic build machine for Debian packages',
      scripts=['debomatic'], ext_modules = [debomaticmodule])
