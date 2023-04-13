# Deb-o-Matic - RemoveChroots module
#
# Copyright (C) 2018-2023 Luca Falavigna
#
# Authors: Luca Falavigna <dktrkranz@debian.org>
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
#
# Remove chroots created long ago

import os
from glob import glob
from shutil import rmtree
from subprocess import check_output as call
from time import time


class DebomaticModule_RemoveChroots:

    def __init__(self):
        pass

    def __purge_chroot(self, distribution, directory):
        architecture = directory.split('-')[1]
        chroots = call(['/usr/bin/schroot', '--all-chroots', '-l'])
        sessions = call(['/usr/bin/schroot', '--all-sessions', '-l'])
        chroot = '{0}-{1}-debomatic'.format(distribution, architecture)
        if chroot in chroots.decode('utf-8'):
            if chroot not in sessions.decode('utf-8'):
                for directory in ('/etc/schroot/chroot.d',
                                  '/etc/sbuild/chroot'):
                    for pattern in ('{0}*'.format(chroot),
                                    '*-{0}-{1}-debomatic*'.format(
                                    architecture, distribution)):
                        for dir in glob(os.path.join(directory, pattern)):
                            if os.path.islink(dir):
                                rmtree(os.readlink(dir))
                            os.unlink(dir)

    def periodic(self, args):
        ctime = time()
        if args.opts.has_section('removechroots'):
            delta = args.opts.getint('removechroots', 'days') * 24 * 60 * 60
            for distribution in os.listdir(args.directory):
                chroot = os.path.join(args.directory,
                                      distribution, distribution)
                if os.path.isdir(chroot):
                    ptime = os.stat(chroot).st_mtime
                    if ptime + delta < ctime:
                        self.__purge_chroot(distribution, args.directory)
