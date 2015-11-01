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
from fcntl import flock, LOCK_EX, LOCK_UN
from subprocess import call, PIPE
from tempfile import NamedTemporaryFile


class DebomaticModule_Repository:

    def __init__(self):
        self.af = '/usr/bin/apt-ftparchive'
        self.gpg = '/usr/bin/gpg'
        self.lockdir = '/var/lib/sbuild/build/.debomatic'

    def pre_build(self, args):
        self.update_repository(args)

    def post_build(self, args):
        self.update_repository(args)

    def pre_chroot(self, args):
        if args.action:
            self.update_repository(args)

    class Lock:

        def __init__(self, distribution, architecture):
            self._file = ('/var/run/debomatic-%s-%s.apt.lock' %
                          (distribution, architecture))

        def __enter__(self):
            self._fd = open(self._file, 'w')
            flock(self._fd, LOCK_EX)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            flock(self._fd, LOCK_UN)
            self._fd.close()

    def update_repository(self, args):
        if args.opts.has_section('repository'):
            gpgkey = args.opts.get('repository', 'gpgkey')
            pubring = args.opts.get('repository', 'pubring')
            secring = args.opts.get('repository', 'secring')
        else:
            return
        if not os.access(self.af, os.X_OK):
            return
        if not os.access(self.gpg, os.X_OK):
            return
        cwd = os.getcwd()
        distribution = args.distribution
        if args.hostarchitecture:
            arch = args.hostarchitecture
        else:
            arch = args.architecture
        archive = args.directory
        pool = os.path.join(archive, 'pool')
        dists = os.path.join(archive, 'dists', distribution)
        packages = os.path.join(dists, 'main', 'binary-%s' % arch)
        packages_file = os.path.join(packages, 'Packages')
        packages_file_tmp = os.devnull
        arch_release_file = os.path.join(packages, 'Release')
        arch_release_file_tmp = os.devnull
        release_file = os.path.join(dists, 'Release')
        release_file_tmp = os.devnull
        release_gpg = os.path.join(dists, 'Release.gpg')
        release_gpg_tmp = os.devnull
        inrelease_gpg = os.path.join(dists, 'InRelease')
        inrelease_gpg_tmp = os.devnull
        for dir in (pool, dists, packages):
            if not os.path.isdir(dir):
                os.makedirs(dir)
        os.chdir(archive)
        with self.Lock(distribution, arch):
            with NamedTemporaryFile('w', dir=packages, delete=False) as fd:
                call([self.af, 'packages', 'pool'], stdout=fd, stderr=PIPE)
                packages_file_tmp = fd.name
            with NamedTemporaryFile('w', dir=packages, delete=False) as fd:
                fd.write('Origin: Deb-O-Matic\n')
                fd.write('Label: Deb-O-Matic\n')
                fd.write('Archive: %s\n' % distribution)
                fd.write('Component: main\n')
                fd.write('Architecture: %s\n' % arch)
                arch_release_file_tmp = fd.name
            with NamedTemporaryFile('w', dir=packages, delete=False) as fd:
                date = datetime.now().strftime('%A, %d %B %Y %H:%M:%S')
                afstring = 'APT::FTPArchive::Release::'
                call([self.af, '-qq',
                      '-o', '%sOrigin=Deb-o-Matic' % afstring,
                      '-o', '%sLabel=Deb-o-Matic' % afstring,
                      '-o', '%sSuite=%s' % (afstring, distribution),
                      '-o', '%sDate=%s' % (afstring, date),
                      '-o', '%sArchitectures=%s' % (afstring, arch),
                      '-o', '%sComponents=main' % afstring,
                      'release', 'dists/%s' % distribution],
                     stdout=fd, stderr=PIPE)
                release_file_tmp = fd.name
            with open(release_file_tmp, 'r+') as fd:
                data = fd.read()
                fd.seek(0)
                fd.write(data.replace('MD5Sum', 'NotAutomatic: yes\nMD5Sum'))
            with NamedTemporaryFile('w', dir=packages, delete=False) as fd:
                call([self.gpg, '--no-default-keyring', '--keyring', pubring,
                      '--secret-keyring', secring, '-u', gpgkey, '--yes',
                      '-a', '-o', fd.name, '-s', release_file_tmp])
                release_gpg_tmp = fd.name
            with NamedTemporaryFile('w', dir=packages, delete=False) as fd:
                call([self.gpg, '--no-default-keyring', '--keyring', pubring,
                      '--secret-keyring', secring, '-u', gpgkey, '--yes',
                      '-a', '-o', fd.name, '--clearsign', release_file])
                inrelease_gpg_tmp = fd.name
            os.rename(packages_file_tmp, packages_file)
            os.rename(arch_release_file_tmp, arch_release_file)
            os.rename(release_file_tmp, release_file)
            os.rename(release_gpg_tmp, release_gpg)
            os.rename(inrelease_gpg_tmp, inrelease_gpg)
        os.chdir(cwd)
