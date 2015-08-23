# Deb-o-Matic - SourceUpload module
#
# Copyright (C) 2014-2015 Luca Falavigna
#
# Authors: Luca Falavigna <dktrkranz@debian.org>
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
# Allows uploading source-only packages to Debian archive

import os
from re import escape, findall, search, sub


class DebomaticModule_SourceUpload:

    def post_build(self, args):
        if not args.success:
            return
        dscfile = None
        changesfile = None
        mirror = args.dists.get(args.distribution, 'mirror')
        try:
            profile = mirror.split('/')[-1]
        except IndexError:
            profile = None
        if profile == 'debian':
            resultdir = os.path.join(args.directory, 'pool', args.package)
            for filename in os.listdir(resultdir):
                if filename.endswith('.dsc'):
                    dscfile = os.path.join(resultdir, filename)
                if filename.endswith('.changes'):
                    changesfile = os.path.join(resultdir, filename)
                    with open(changesfile) as fd:
                        arch = set(findall('Architecture: (.*)',
                                   fd.read())[0].split())
                        if arch.issubset({'source', 'all'}):
                            changesfile = None
            if dscfile and changesfile:
                with open(dscfile, 'r') as fd:
                    dsc = fd.read()
                if search('Package-List:', dsc):
                    with open(changesfile, 'r') as fd:
                        cf = fd.read()
                        arch = findall('Architecture: (.*)', cf)[0].split()
                        if 'source' in arch:
                            arch = {'source', 'all'}.intersection(arch)
                            cf = sub('Architecture: .*',
                                     'Architecture: %s' % ' '.join(arch), cf)
                            for deb in findall(' .* \S+_\S+_\S+.u?deb', cf):
                                if (not deb.endswith('_all.deb') and
                                   not deb.endswith('_all.udeb')):
                                    cf = sub(escape(deb) + '\n', '', cf)
                            sourcecf = sub('_[^_]+?.changes',
                                           '_sourceupload.changes',
                                           changesfile)
                            with open(sourcecf, 'w') as sourcecf:
                                sourcecf.write(cf)
                                sourcecf.flush()
