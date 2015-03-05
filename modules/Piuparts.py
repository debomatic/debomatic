# Deb-o-Matic - PiuParts module
#
# Copyright (C) 2012 Leo Iannacone
# Copyright (C) 2015 Luca Falavigna
#
# Authors: Leo Iannacone <l3on@ubuntu.com>
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
#
# Check through piuparts if packages can be installed/upgraded/removed.

import os
from subprocess import call


class DebomaticModule_Piuparts:

    def __init__(self):
        self.piuparts = '/usr/sbin/piuparts'

    def post_build(self, args):
        if not args.success:
            return
        if not os.access(self.piuparts, os.X_OK):
            return
        if args.opts.has_section('piuparts'):
            options = args.opts.get('piuparts', 'options').strip().split()
        else:
            options = []
        distribution = args.distribution
        mirror = args.dists.get(distribution, 'mirror')
        schroot = '%s-%s-debomatic' % (distribution, args.architecture)
        resultdir = os.path.join(args.directory, 'pool', args.package)
        for filename in os.listdir(resultdir):
            if filename.endswith('.changes'):
                log = os.path.join(resultdir, args.package) + '.piuparts'
                with open(log, 'a') as fd:
                    cmd = [self.piuparts,
                           '-I', 'sys/fs/aufs/*',
                           '-I', 'build/*',
                           '-d', '%s' % distribution,
                           '-D', '%s' % mirror.split('/')[-1],
                           '--schroot=chroot:%s' % schroot,
                           os.path.join(resultdir, filename)]
                    for option in options:
                        cmd.insert(-1, option)
                    call(cmd, stdout=fd)
                break
