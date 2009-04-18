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

    def write_pkg_info(self, option, deblist, contents_file):
        for deb in deblist:
            os.system("echo '%s:' >> %s" % (deb, contents_file))
            os.system('%s %s %s >> %s' % (self.dpkg, option, deb, contents_file))
            os.system("echo >> %s" % contents_file)

    def post_build(self, args):
        resultdir = os.path.join(args['directory'], 'pool', args['package'])
        contents_file = os.path.join(resultdir, args['package']) + '.contents'
        try:
            os.stat(contents_file)
            os.remove(contents_file)
        except OSError:
            pass # Nothing to do

        deblist = \
            map(
                lambda filename: os.path.join(resultdir, filename),
                filter(lambda filename: filename.endswith('.deb'), os.listdir(resultdir))
                )

        self.write_pkg_info('-I', deblist, contents_file)
        self.write_pkg_info('-c', deblist, contents_file)

