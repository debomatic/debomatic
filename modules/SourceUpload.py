# Deb-o-Matic - SourceUpload module
#
# Copyright (C) 2014-2023 Luca Falavigna
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
# Allows uploading source-only packages to Debian archive

import os
from re import match, sub


class DebomaticModule_SourceUpload:

    def post_build(self, args):
        if not args.success:
            return
        lines = []
        changesfile = None
        resultdir = os.path.join(args.directory, 'pool', args.package)
        for filename in os.listdir(resultdir):
            if filename.endswith('.changes'):
                changesfile = os.path.join(resultdir, filename)
                break
        if changesfile:
            with open(changesfile, 'r') as fd:
                cf = fd.read()
            for line in cf.split('\n'):
                if match(r'.*?\S+_\S+_\S+\.u?deb', line):
                    continue
                elif line.startswith('Architecture: '):
                    lines.append('Architecture: source')
                else:
                    lines.append(line)
            sourcecf = sub('_[^_]+?.changes',
                           '_sourceupload.changes', changesfile)
            with open(sourcecf, 'w') as sourcecf:
                sourcecf.write('\n'.join(lines))
