# Deb-o-Matic - Contents module
#
# Copyright (C) 2009 Alessio Treglia
#
# Authors: Alessio Treglia <quadrispro@ubuntu.com>
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
# Store dpkg -c *.deb and dpkg -I *.deb outputs in the pool directory.

import os

class DebomaticModule_Contents:

    def __init__(self):
        self.dpkg = "/usr/bin/dpkg"

    def post_build(self, args):
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        contents = os.path.join(resultdir, args['package']) + '.contents'
        try:
            os.stat(contents)
            os.remove(contents)
        except OSError:
            pass
        for filename in os.listdir(resultdir):
            if filename.endswith('.deb'):
                pkg_name = os.path.join(resultdir, filename)
                os.system("echo 'Running dpkg on %s:' >> %s" % (pkg_name, contents))
                os.system('%s -I %s >> %s' % (self.dpkg, pkg_name, contents))
                os.system('%s -c %s >> %s' % (self.dpkg, pkg_name, contents))
                os.system("echo '------------------------------- END -------------------------------' >> %s" % contents)
