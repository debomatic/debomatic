# Deb-o-Matic - Package build path cleaner
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
# Delete all files generated by previous build.

import os


class DebomaticModule_PrevBuildCleaner:

    def pre_build(self, args):
        exts_to_clean = ['.deb', '.ddeb', '.gz', '.bz2', '.lzma', '.xz',
                        '.dsc', '.contents', '.lintian', '.changes']
        pkg_build_path = '%(directory)s/pool/%(package)s' % args
        for filename in os.listdir(pkg_build_path):
            name, ext = os.path.splitext(filename)
            if ext in exts_to_clean:
                os.remove(os.path.join(pkg_build_path, filename))
