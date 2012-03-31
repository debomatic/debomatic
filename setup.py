#!/usr/bin/python
# Deb-o-Matic
#
# Copyright (C) 2007-2012 Luca Falavigna
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
from distutils.command.install_data import install_data
from glob import glob
from subprocess import call


for po in glob(os.path.join('po', '*.po')):
    mo = os.path.join('locale', os.path.splitext(os.path.basename(po))[0],
                      'LC_MESSAGES/debomatic.mo')
    if not os.path.isdir(os.path.dirname(mo)):
        os.makedirs(os.path.dirname(mo))
    call(['msgfmt', '-o', mo, po])


class InstallGuide(install_data):

    def run(self):
        call(['make', '-C', 'docs', 'latexpdf'])
        self.data_files.extend([('share/doc/debomatic',
                                 ['docs/_build/latex/Deb-o-Matic.pdf'])])
        install_data.run(self)


def install_files(rootdir, prefix=''):
    filelist = []
    for root, subFolders, files in os.walk(rootdir):
        dirlist = []
        for file in files:
            dirlist.append(os.path.join(root, file))
        if dirlist:
            filelist.append((os.path.join(prefix, root), dirlist))
    return filelist


setup(name='debomatic',
      version = '0.10',
      author = 'Luca Falavigna',
      author_email = 'dktrkranz@debian.org',
      description = 'Automatic build machine for Debian source packages',
      url = 'https://launchpad.net/debomatic/',
      license = 'GNU GPL',
      packages = ['Debomatic'],
      scripts = ['debomatic'],
      data_files = [('share/man/man1', ['docs/debomatic.1'])] +
                   install_files('etc', '/') +
                   install_files('modules', 'share/debomatic') +
                   install_files('pbuilderhooks', 'share/debomatic') +
                   install_files('locale', 'share'),
      cmdclass = {'install_data': InstallGuide})
