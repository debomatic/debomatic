# Deb-o-Matic - Lintian module
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2008-2014 Luca Falavigna
#
# Authors: David Futcher <bobbo@ubuntu.com>
#          Luca Falavigna <dktrkranz@debian.org>
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
# Stores litian output on top of the built package in the pool directory.

import os
from subprocess import call


class DebomaticModule_Lintian:

    def __init__(self):
        self.lintian = '/usr/bin/lintian'

    def post_build(self, args):
        changesfile = None
        if args['opts'].has_section('lintian'):
            lintopts = args['opts'].get('lintian', 'lintopts').strip()
        else:
            lintopts = []
        with open(args['cfg'], 'r') as fd:
            for line in [line.strip() for line in fd.readlines()]:
                if 'MIRRORSITE' in line:
                    try:
                        profile = line.split('/')[-1]
                    except IndexError:
                        profile = None
                    if profile:
                        lintopts += ' --profile %s' % profile
                    break
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        lintian = os.path.join(resultdir, args['package']) + '.lintian'
        for filename in os.listdir(resultdir):
            if filename.endswith('.changes'):
                changesfile = os.path.join(resultdir, filename)
                break
        if changesfile:
            with open(lintian, 'w') as fd:
                call([self.lintian, '-V'], stdout=fd)
                fd.write('Options: %s\n\n' % lintopts)
                fd.flush()
                cmd = [self.lintian] + lintopts.split() + [changesfile]
                call(cmd, stdout=fd)
