# Deb-o-Matic - Contents module
#
# Copyright (C) 2011-2015 Luca Falavigna
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
from datetime import datetime
from subprocess import call, PIPE


class DebomaticModule_Repository:

    def __init__(self):
        self.af = '/usr/bin/apt-ftparchive'
        self.gpg = '/usr/bin/gpg'

    def pre_build(self, args):
        self.update_repository(args)

    def post_build(self, args):
        self.update_repository(args)

    def pre_chroot(self, args):
        if args.action:
            self.update_repository(args)

    def update_repository(self, args):
        if args.opts.has_section('repository'):
            gpgkey = args.opts.get('repository', 'gpgkey')
            pubring = args.opts.get('repository', 'pubring')
            secring = args.opts.get('repository', 'secring')
        else:
            return
        cwd = os.getcwd()
        if not os.path.isfile(self.af):
            return
        distribution = args.distribution
        arch = args.architecture
        archive = args.directory
        pool = os.path.join(archive, 'pool')
        dists = os.path.join(archive, 'dists', distribution)
        packages = os.path.join(dists, 'main', 'binary-%s' % arch)
        packages_file = os.path.join(packages, 'Packages')
        arch_release_file = os.path.join(packages, 'Release')
        release_file = os.path.join(dists, 'Release')
        release_gpg = os.path.join(dists, 'Release.gpg')
        inrelease_gpg = os.path.join(dists, 'InRelease')
        for dir in (pool, dists, packages):
            if not os.path.isdir(dir):
                os.makedirs(dir)
        os.chdir(archive)
        with open(packages_file, 'w') as fd:
            call([self.af, 'packages', 'pool'], stdout=fd, stderr=PIPE)
        with open(arch_release_file, 'w') as fd:
            fd.write('Origin: Deb-O-Matic\n')
            fd.write('Label: Deb-O-Matic\n')
            fd.write('Archive: %s\n' % distribution)
            fd.write('Component: main\n')
            fd.write('Architecture: %s\n' % arch)
        with open(release_file, 'w') as fd:
            date = datetime.now().strftime('%A, %d %B %Y %H:%M:%S')
            call([self.af, '-qq',
                  '-o', 'APT::FTPArchive::Release::Origin=Deb-o-Matic',
                  '-o', 'APT::FTPArchive::Release::Label=Deb-o-Matic',
                  '-o', 'APT::FTPArchive::Release::Suite=%s' % distribution,
                  '-o', 'APT::FTPArchive::Release::Date=%s' % date,
                  '-o', 'APT::FTPArchive::Release::Architectures=%s' % arch,
                  '-o', 'APT::FTPArchive::Release::Components=main',
                  'release', 'dists/%s' % distribution],
                 stdout=fd, stderr=PIPE)
        with open(release_file, 'r+') as fd:
            data = fd.read()
            fd.seek(0)
            fd.write(data.replace('MD5Sum', 'NotAutomatic: yes\nMD5Sum'))
        call([self.gpg, '--no-default-keyring', '--keyring', pubring,
              '--secret-keyring', secring, '-u', gpgkey, '--yes', '-a',
              '-o', release_gpg, '-s', release_file])
        call([self.gpg, '--no-default-keyring', '--keyring', pubring,
              '--secret-keyring', secring, '-u', gpgkey, '--yes', '-a',
              '-o', inrelease_gpg, '--clearsign', release_file])
        os.chdir(cwd)
