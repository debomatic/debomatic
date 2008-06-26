#!/usr/bin/env python
# Deb-o-Matic
#
# Copyright (C) 2007-2008 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

from distutils.core import setup
   
setup(name='debomatic',
      version="0.5",
      author='Luca Falavigna',
      author_email='dktrkranz@ubuntu.com',
      description='Automatic build machine for Debian source packages',
      url = 'https://launchpad.net/debomatic/',
      license='GNU GPL',
      packages=['Debomatic'],
      scripts=['debomatic'])
