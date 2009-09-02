#!/usr/bin/env python
# Deb-o-Matic
#
# Copyright (C) 2007-2009 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
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

import os
from distutils.core import setup

def install_files(rootdir, prefix=''):
    filelist = list()
    for root, subFolders, files in os.walk(rootdir):
        dirlist = list()
        for file in files:
            dirlist.append(os.path.join(root, file))
        if len(dirlist):
            filelist.append((os.path.join(prefix, root),dirlist))
    return filelist
   
setup(name='debomatic',
      version="0.7",
      author='Luca Falavigna',
      author_email='dktrkranz@debian.org',
      description='Automatic build machine for Debian source packages',
      url = 'https://launchpad.net/debomatic/',
      license='GNU GPL',
      packages=['Debomatic'],
      scripts=['debomatic'],
      data_files=[('share/man/man1', ['docs/debomatic.1']),
                  ('share/man/man5', ['docs/debomatic.conf.5']),
                  ('share/doc/debomatic', ['docs/ExampleModule.py', 'docs/guide.html', 'docs/guide.txt'])] + \
                  install_files('etc', '/') + install_files('modules', 'share/debomatic'))
