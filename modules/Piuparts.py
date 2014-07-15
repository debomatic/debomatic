# Deb-o-Matic - PiuParts module
#
# Copyright (C) 2012 Leo Iannacone
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
from re import findall


class DebomaticModule_Piuparts:

    def __init__(self):
        self.piuparts = '/usr/sbin/piuparts'

    def post_build(self, args):
        if not args['success']:
            return
        if args['opts'].has_section('piuparts'):
            piupopts = args['opts'].get('piuparts', 'piupopts').strip().split()
        else:
            piupopts = []
        with open(args['cfg'], 'r') as fd:
            data = fd.read()
            distribution = findall('[^#]?DISTRIBUTION="?(.*[^"])"?\n', data)[0]
            mirror = findall('[^#]?MIRRORSITE="?(.*[^"])"?\n', data)[0]
            components = findall('[^#]?COMPONENTS="?(.*[^"])"?\n', data)[0]
        piupopts += ['-e', '%(directory)s/%(distribution)s' % args]
        piupopts += ['-d', '%s' % distribution]
        piupopts += ['-m', '%s %s' % (mirror, components)]
        piupopts += ['-D', '%s' % mirror.split('/')[-1]]
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        for filename in os.listdir(resultdir):
            if filename.endswith('.changes'):
                piupartsout = os.path.join(resultdir,
                                           args['package']) + '.piuparts'
                with open(piupartsout, 'w') as fd:
                    cmd = [self.piuparts] + piupopts + \
                          [os.path.join(resultdir, filename)]
                    call(cmd, stdout=fd)
                break
