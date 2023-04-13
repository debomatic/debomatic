#!/usr/bin/python3
# Deb-o-Matic
#
# Copyright (C) 2007-2023 Luca Falavigna
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
from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.dir_util import mkpath
from distutils.file_util import copy_file
from glob import glob
from re import sub
from subprocess import call


for po in glob(os.path.join('po', '*.po')):
    mo = os.path.join('locale', os.path.splitext(os.path.basename(po))[0],
                      'LC_MESSAGES/debomatic.mo')
    if not os.path.isdir(os.path.dirname(mo)):
        os.makedirs(os.path.dirname(mo))
    call(['msgfmt', '-o', mo, po])


class SbuildCommands():

    def __init__(self):
        self.directories = ('build-deps-failed-commands',
                            'build-failed-commands',
                            'chroot-cleanup-commands',
                            'chroot-setup-commands',
                            'finished-build-commands',
                            'post-build-commands',
                            'pre-build-commands',
                            'starting-build-commands')

    def __enter__(self):
        for directory in self.directories:
            try:
                os.mkdir(os.path.join('sbuildcommands', directory))
            except FileExistsError:
                pass
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for directory in self.directories:
            try:
                os.rmdir(os.path.join('sbuildcommands', directory))
            except OSError:
                pass


class InstallData(install_data):

    def run(self):
        call(['make', '-C', 'docs', 'latexpdf'])
        self.data_files.extend([('share/doc/debomatic',
                                 ['docs/_build/latex/Deb-o-Matic.pdf'])])
        self.install_files('etc')
        self.install_files('usr')
        self.install_files('modules', 'share/debomatic')
        with SbuildCommands():
            self.install_files('sbuildcommands', 'share/debomatic', True)
        self.install_files('locale', 'share')
        install_data.run(self)
        mkpath(os.path.join(self.install_dir, 'sbin'))
        if os.path.isabs(self.install_dir):
            install_dir = self.install_dir
        else:
            install_dir = os.path.join(os.getcwd(), self.install_dir)
        dstlink = os.path.join(install_dir, 'sbin/debomatic')
        if os.path.islink(dstlink):
            os.remove(dstlink)
        copy_file(os.path.join(install_dir, 'share/debomatic/debomatic'),
                  dstlink, link='sym')

    def install_files(self, rootdir, prefix='', empty=False):
        filelist = []
        for root, subFolders, files in os.walk(rootdir):
            dirlist = []
            for file in files:
                dirlist.append(os.path.join(root, file))
            if dirlist or empty:
                filelist.append((os.path.join(prefix, root), dirlist))
        if not prefix:
            orig_prefix = self.install_dir
            orig_data_files = self.data_files
            self.install_dir = sub('/*usr/*$', '/', self.install_dir)
            self.data_files = filelist
            install_data.run(self)
            self.install_dir = orig_prefix
            self.data_files = orig_data_files
        else:
            self.data_files.extend(filelist)


setup(name='debomatic',
      version='0.26',
      author='Luca Falavigna',
      author_email='dktrkranz@debian.org',
      description='Automatic build machine for Debian source packages',
      url='http://debomatic.github.io',
      license='GNU GPL',
      packages=['Debomatic'],
      data_files=[('share/debomatic', ['debomatic']),
                  ('share/man/man1', ['docs/debomatic.1'])],
      cmdclass={'install_data': InstallData})
