#!/usr/bin/env python

# Deb-o-Matic
#
# Copyright (C) 2007 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; only version 2 of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from distutils.core import setup, Extension
   
debomaticmodule = Extension('debomatic', sources = ['debomaticmodule.c'])

setup(name='debomatic', version="0.1",
      description = 'Automatic build machine for Debian packages',
      scripts=['debomatic'], ext_modules = [debomaticmodule])
