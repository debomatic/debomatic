# Deb-o-Matic - Blhc module
#
# Copyright (C) 2014 Mattia Rizzolo
#
# Authors: Mattia Rizzolo <mattia@mapreri.org>
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
# Stores blhc output on top of the built package in the pool directory.

import os
from logging import error
from subprocess import getstatusoutput


class DebomaticModule_Blhc:

    def __init__(self):
        self.blhc = '/usr/bin/blhc'

    def post_build(self, args):
        if args['opts'].has_section('blhc') and \
           args['opts'].has_option('blhc', 'blhcopts'):
            blhcopts = args['opts'].get('blhc', 'blhcopts').strip().split()
        else:
            blhcopts = []
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        buildlog = os.path.join(resultdir, args['package']) + '.buildlog'
        blhclog = os.path.join(resultdir, args['package']) + '.blhc'
        if os.access(buildlog, os.R_OK):
            if os.access(self.blhc, os.X_OK):
                cmd = [self.blhc] + blhcopts + [buildlog]
                exitcode, output = getstatusoutput(' '.join(cmd))
                # Never write bhlc log if no useful information has been
                # reported, exit statuses:
                # 0:   Buildlog is OK
                # 1:   No compiler commands were found
                if exitcode in [0, 1]:
                    return
                # else, write the report
                elif len(output) > 0:
                    with open(blhclog, 'w') as fd:
                        fd.write(output)
            else:
                error(_('blhc binary is not available'))
