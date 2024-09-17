# Deb-o-Matic - UpdateChroots module
#
# Copyright (C) 2018-2024 Luca Falavigna
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
# Update chroots

import os
from glob import glob
from re import findall, DOTALL
from subprocess import check_output as call
from time import time


class DebomaticModule_UpdateChroots:

    def __init__(self):
        pass

    def __architecture(self, args):
        architecture = False
        if (args.opts.has_section('crossbuild') and
                args.opts.getboolean('crossbuild', 'crossbuild')):
            architecture = args.opts.get('crossbuild',
                                         'hostarchitecture')
        else:
            architecture = args.opts.get('debomatic', 'architecture')
            if architecture == 'system':
                b_arch = call(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
                architecture = b_arch.strip().decode('utf-8')
        return architecture

    def __timestamp(self, filename, delta):
        current = time()
        try:
            with open(filename) as fd:
                last = float(fd.read().strip())
                if (current - last > delta):
                    with open(filename, 'w') as fd:
                        fd.write('{0}\n'.format(current))
                    return True
                else:
                    return False
        except FileNotFoundError:
            with open(filename, 'w') as fd:
                fd.write('{0}\n'.format(current))
            return False

    def periodic(self, args):
        if args.opts.has_section('updatechroots'):
            delta = args.opts.getint('updatechroots', 'days') * 24 * 60 * 60
            chroots = call(['/usr/bin/schroot', '--all-chroots', '-l'])
            arch = self.__architecture(args)
            chroots = findall(r'chroot:(\S+?-{0}-debomatic)\n?'.format(arch),
                              chroots.decode('utf-8'))
            for chroot in glob('/etc/schroot/chroot.d/*-debomatic-*'):
                with open(chroot) as fd:
                    content = fd.read()
                (name, path) = findall(r'\[(\S+?)\].*directory=(\S+)',
                                       content, DOTALL)[0]
                if name in chroots:
                    tag = os.path.join(path, '.debomatic')
                    if self.__timestamp(tag, delta):
                        call(['/usr/bin/sbuild-update', '-udcar',
                              '--arch={0}'.format(arch), name])
