# Deb-o-Matic - Repository module
#
# Copyright (C) 2011-2025 Luca Falavigna
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
# Generate local repository of built packages

import os
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_SH, LOCK_UN
from shutil import rmtree
from stat import S_IRWXU, S_IRGRP, S_IXGRP, S_IROTH, S_IXOTH
from subprocess import Popen, PIPE
from tempfile import mkdtemp, mkstemp


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

    class Lock:

        def __init__(self, distribution, architecture):
            self._file = ('/tmp/debomatic-%s-%s.apt.lock' %
                          (distribution, architecture))
            self._skip = False

        def __enter__(self):
            self._fd = open(self._file, 'w')
            try:
                flock(self._fd, LOCK_EX | LOCK_NB)
            except IOError:
                flock(self._fd, LOCK_SH)
                self._skip = True
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            flock(self._fd, LOCK_UN)
            self._fd.close()

        def skip(self):
            return self._skip

    def update_repository(self, args):
        if args.opts.has_section('repository'):
            gpgkey = args.opts.get('repository', 'gpgkey')
            keyring = args.opts.get('repository', 'keyring')
        else:
            return
        if not os.access(self.af, os.X_OK):
            return
        if not os.access(self.gpg, os.X_OK):
            return
        distribution = os.path.basename(args.directory)
        archive = args.directory
        pool = os.path.join(archive, 'pool')
        distslink = os.path.join(archive, 'dists', distribution)
        if not os.path.islink(distslink):
            if not os.path.isdir(os.path.join(archive, 'dists')):
                os.makedirs(os.path.join(archive, 'dists'))
            tmpdir = mkdtemp(prefix='.', dir=os.path.join(archive, 'dists'))
            os.symlink(tmpdir, distslink)
        dists = mkdtemp(prefix='.', dir=os.path.join(archive, 'dists'))
        for arch in [a for a in (args.architecture,
                                 args.hostarchitecture) if a is not None]:
            packages = os.path.join(dists, 'main', 'binary-%s' % arch)
            packages_file = os.path.join(packages, 'Packages')
            arch_release_file = os.path.join(packages, 'Release')
            release_file = os.path.join(dists, 'Release')
            release_gpg = os.path.join(dists, 'Release.gpg')
            inrelease_gpg = os.path.join(dists, 'InRelease')
            for dir in (pool, packages):
                if not os.path.isdir(dir):
                    os.makedirs(dir)
            with self.Lock(distribution, arch) as lock:
                if not lock.skip():
                    with open(packages_file, 'w') as fd:
                        Popen([self.af, '-a', arch, 'packages', 'pool'],
                              stdout=fd, stderr=PIPE, cwd=archive).wait()
                    with open(arch_release_file, 'w') as fd:
                        fd.write('Origin: Deb-O-Matic\n')
                        fd.write('Label: Deb-O-Matic\n')
                        fd.write('Archive: %s\n' % distribution)
                        fd.write('Component: main\n')
                        fd.write('Architecture: %s\n' % arch)
                    with open(release_file, 'w') as fd:
                        afstring = 'APT::FTPArchive::Release::'
                        Popen([self.af, '-qq',
                               '-o', '%sOrigin=Deb-o-Matic' % afstring,
                               '-o', '%sLabel=Deb-o-Matic' % afstring,
                               '-o', '%sSuite=%s' % (afstring, distribution),
                               '-o', '%sArchitectures=%s' % (afstring, arch),
                               '-o', '%sComponents=main' % afstring,
                               'release',
                               'dists/%s' % os.path.basename(dists)],
                              stdout=fd, stderr=PIPE, cwd=archive).wait()
                    with open(release_file, 'r+') as fd:
                        data = fd.read()
                        fd.seek(0)
                        fd.write(data.replace('MD5Sum',
                                 'NotAutomatic: yes\nMD5Sum'))
                with open(release_gpg, 'w') as fd:
                    Popen([self.gpg, '--no-default-keyring', '--homedir',
                           keyring, '-u', gpgkey, '--yes', '-a', '-o', fd.name,
                           '-b', release_file], cwd=archive).wait()
                with open(inrelease_gpg, 'w') as fd:
                    Popen([self.gpg, '--no-default-keyring', '--homedir',
                           keyring, '-u', gpgkey, '--yes', '-a', '-o', fd.name,
                           '--clearsign', release_file], cwd=archive).wait()
        olddists = os.readlink(distslink)
        (tmp, tmplink) = mkstemp(prefix='.',
                                 dir=os.path.dirname(olddists))
        os.close(tmp)
        os.unlink(tmplink)
        os.symlink(dists, tmplink)
        os.chmod(dists, S_IRWXU | S_IRGRP | S_IXGRP |
                 S_IROTH | S_IXOTH)
        os.rename(tmplink, distslink)
        try:
            rmtree(olddists)
        except FileNotFoundError:
            pass
