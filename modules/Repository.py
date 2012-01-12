# Deb-o-Matic - Contents module
#
# Copyright (C) 2011-2012 Luca Falavigna
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
# Generate local repository of built packages

import os
from subprocess import call, PIPE


class DebomaticModule_Repository:

    def __init__(self):
        self.af = '/usr/bin/apt-ftparchive'
        self.gzip = '/bin/gzip'

    def post_build(self, args):
        cwd = os.getcwd()
        if not os.path.isfile(self.af):
            return
        pool_dir = os.path.join(args['directory'], 'pool')
        packages_file = os.path.join(pool_dir, 'Packages')
        release_file = os.path.join(pool_dir, 'Release')
        os.chdir(pool_dir)
        with open(packages_file, 'w') as fd:
            call([self.af, 'packages', '.'], stdout=fd, stderr=PIPE)
        call([self.gzip, '-9', '-f', packages_file], stdout=PIPE, stderr=PIPE)
        with open(release_file, 'w') as fd:
            call([self.af, '-qq',
                 '-o', 'APT::FTPArchive::Release::Origin="Deb-o-Matic"',
                 '-o', 'APT::FTPArchive::Release::Label="%s"' % \
                       args['distribution'],
                 'release', '.'], stdout=fd, stderr=PIPE)
        with open(release_file, 'r+') as fd:
            data = fd.read()
            fd.seek(0)
            fd.write(data.replace('MD5Sum', 'NotAutomatic: yes\nMD5Sum'))
        os.chdir(cwd)
