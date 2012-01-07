# Deb-o-Matic - Contents module
#
# Copyright (C) 2009 Alessio Treglia
# Copyright (C) 2010-2012 Luca Falavigna
#
# Authors: Alessio Treglia <quadrispro@ubuntu.com>
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
# Store debc output in the pool directory.

import os
from subprocess import call


class DebomaticModule_Contents:

    def __init__(self):
        self.debc = '/usr/bin/debc'

    def post_build(self, args):
        changes_file = None
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        contents_file = os.path.join(resultdir, args['package']) + '.contents'
        for filename in os.listdir(resultdir):
            if filename.endswith('.changes'):
                changes_file = os.path.join(resultdir, filename)
                break
        if changes_file:
            with open(contents_file, 'w') as fd:
                call([self.debc, changes_file], stdout=fd)
