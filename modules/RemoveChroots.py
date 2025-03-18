# Deb-o-Matic - RemoveChroots module
#
# Copyright (C) 2018-2024 Luca Falavigna
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
# Remove chroots created long ago

import os
from glob import glob
from pathlib import Path
from time import time


class DebomaticModule_RemoveChroots:

    def __init__(self):
        pass

    def periodic(self, args):
        ctime = time()
        if args.opts.has_section('removechroots'):
            delta = args.opts.getint('removechroots', 'days') * 24 * 60 * 60
            for chroot in glob(f'{Path.home()}/.cache/sbuild/*-debomatic.*'):
                ptime = os.stat(chroot).st_mtime
                if ptime + delta < ctime:
                    os.unlink(chroot)
