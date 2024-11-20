# Deb-o-Matic - Reprepro module
#
# Copyright (C) 2011-2015 Luca Falavigna
#                    2016 Niko Tyni
#
# Authors: Niko Tyni <ntyni@debian.org>
#
# Based on the Repository and Lintian modules
#  by Luca Falavigna <dktrkranz@debian.org>
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
# Generate a local reprepro repository of built packages

import os
from subprocess import call
from logging import debug, error, info


class DebomaticModule_Reprepro:

    def __init__(self):
        self.reprepro = '/usr/bin/reprepro'
        self.before   = [ 'BuildCleaner' ]

    def post_build(self, args):
        self.update_repository(args)

    def update_repository(self, args):
        if not args.success:
            debug('Build failed, nothing to add with Reprepro')
            return

        binary = None
        basedir = None
        dists = []

        if args.opts.has_section('reprepro'):
            if args.opts.has_option('reprepro', 'basedir'):
                basedir = args.opts.get('reprepro', 'basedir')
            if args.opts.has_option('reprepro', 'binary'):
                binary  = args.opts.get('reprepro', 'binary')
            if args.opts.has_option('reprepro', 'dists'):
                dists = args.opts.get('reprepro', 'dists').split()

        if dists and not args.distribution in dists:
            debug('Distribution %s not in Reprepro dists list, skipping' % args.distribution)
            return

        info('Adding build result to reprepro dist %s' % args.distribution)

        if binary:
            self.reprepro = binary

        cmd = [self.reprepro,
               '--ignore=surprisingbinary',
               '--ignore=missingfile',
               '--waitforlock=10',
               'include',
               args.distribution]

        if basedir:
            cmd[1:1] = ['--basedir', basedir ]

        changesfile = None
        resultdir = os.path.join(args.directory, 'pool', args.package)
        files = os.listdir(resultdir)
        for filename in files:
            if filename.endswith('.changes'):
                changesfile = os.path.join(resultdir, filename)
                break

        if changesfile and os.access(self.reprepro, os.X_OK):
            info('calling %s on %s' % (self.reprepro, changesfile))
            cmd.append(changesfile)
            call(cmd)
        else:
            if not changesfile:
                info('missing .changes? aborting')
            if not os.access(self.reprepro, os.X_OK):
                info('binary %s not accessible? aborting' % self.reprepro)

