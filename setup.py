#!/usr/bin/python3
# Deb-o-Matic
#
# Copyright (C) 2007-2025 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option), any later version.
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
from glob import glob
from setuptools import setup
from setuptools.command.build import build
from setuptools.command.install import install
from subprocess import call


data_files = []


class Build(build, object):

    def run(self):
        super(Build, self).run()
        for po in glob(os.path.join('po', '*.po')):
            mo = os.path.join('locale',
                              os.path.splitext(os.path.basename(po))[0],
                              'LC_MESSAGES/debomatic.mo')
            if not os.path.isdir(os.path.dirname(mo)):
                os.makedirs(os.path.dirname(mo))
            call(['msgfmt', '-o', mo, po])
        call(['make', '-C', 'docs', 'latexpdf'])


class Install(install, object):

    def run(self):
        data_files.append(('share/debomatic', ['debomatic']))
        data_files.append(('share/man/man1', ['docs/debomatic.1']))
        data_files.append(('share/doc/debomatic',
                           ['docs/_build/latex/Deb-o-Matic.pdf']))
        self.add_content('modules', 'share/debomatic')
        self.add_content('etc', '/')
        self.add_content('usr', '/')
        self.add_content('sbuildcommands', 'share/debomatic')
        self.add_content('locale', 'share')
        super(Install, self).run()

    def add_content(self, rootdir, prefix):
        for root, subFolders, files in os.walk(rootdir):
            for file in files:
                data_files.append((os.path.join(prefix, root),
                                   [os.path.join(root, file)]))


setup(name='debomatic',
      version='0.26',
      author='Luca Falavigna',
      author_email='dktrkranz@debian.org',
      description='Automatic build machine for Debian source packages',
      url='https://debomatic.github.io',
      license='GNU GPL',
      packages=['Debomatic'],
      data_files=data_files,
      cmdclass={'build': Build,
                'install': Install})
