# Deb-o-Matic - Lintian module
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2008-2010 Luca Falavigna
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
from re import findall
from Debomatic import Options

class DebomaticModule_Lintian:

    def __init__(self):
        self.lintian = "/usr/bin/lintian"

    def post_build(self, args):
        changesfile = None
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        lintian = os.path.join(resultdir, args['package']) + '.lintian'
        for filename in os.listdir(resultdir):
            result = findall('.*.changes', filename)
            if len(result):
                changesfile = os.path.join(resultdir, result[0])
                break
        if changesfile:
            os.system('%s -V > %s' % (self.lintian, lintian))
            os.system('%s --allow-root -i -I -E --pedantic %s >> %s' % (self.lintian, changesfile, lintian))

