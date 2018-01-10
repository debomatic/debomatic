# Deb-o-Matic - Lintian module
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2008-2018 Luca Falavigna
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
from shutil import copyfile
from subprocess import call, PIPE


class DebomaticModule_Lintian:

    def __init__(self):
        self.lintian = '/usr/bin/lintian'

    def post_build(self, args):
        if not args.success:
            return
        changesfile = None
        if args.opts.has_section('lintian'):
            lintopts = args.opts.get('lintian', 'options').strip()
        else:
            lintopts = []
        mirror = args.dists.get(args.distribution, 'mirror')
        try:
            profile = mirror.split('/')[-1]
        except IndexError:
            profile = None
        if profile:
            lintopts += ' --profile %s' % profile
        resultdir = os.path.join(args.directory, 'pool', args.package)
        lintian = os.path.join(resultdir, args.package) + '.lintian'
        files = os.listdir(resultdir)
        for filename in files:
            if filename.endswith('.changes'):
                changesfile = os.path.join(resultdir, filename)
                break
        tempfiles = set()
        for file in [f for f in args.files if not f.endswith('.changes')]:
            if not os.path.basename(file) in files:
                copyfile(file, os.path.join(resultdir, os.path.basename(file)))
                tempfiles.add(os.path.join(resultdir, os.path.basename(file)))
        if changesfile and os.access(self.lintian, os.X_OK):
            with open(lintian, 'w') as fd:
                call([self.lintian, '-V'], stdout=fd)
                fd.write('Options: %s\n\n' % lintopts)
                fd.flush()
                cmd = [self.lintian] + lintopts.split() + [changesfile]
                call(cmd, stdout=fd, stderr=PIPE)
        for file in tempfiles:
            os.remove(file)
