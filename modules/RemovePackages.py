# Deb-o-Matic - RemovePackages module
#
# Copyright (C) 2018-2022 Luca Falavigna
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
# Remove packages built long ago

import os
from shutil import rmtree
from time import time


class DebomaticModule_RemovePackages:

    def __init__(self):
        pass

    def periodic(self, args):
        ctime = time()
        if args.opts.has_section('removepackages'):
            delta = args.opts.getint('removepackages', 'days') * 24 * 60 * 60
            if os.path.isdir(args.directory):
                for suite in os.listdir(args.directory):
                    element = os.path.join(args.directory, suite)
                    pool = os.path.join(element, 'pool')
                    if os.path.isdir(pool):
                        for package in os.listdir(pool):
                            package = os.path.join(pool, package)
                            if os.path.isdir(package):
                                ptime = os.stat(package).st_mtime
                                if ptime + delta < ctime:
                                    rmtree(package)
                        if not os.listdir(pool):
                            rmtree(pool)
                    if os.path.isdir(element):
                        if not [f for f in os.listdir(element)
                                if f != 'dists' and f != 'logs']:
                            rmtree(element)
