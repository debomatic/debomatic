# Deb-o-Matic - AutoPkgTest module
#
# Copyright (C) 2014 Leo Iannacone
# Copyright (C) 2015 Luca Falavigna
#
# Authors: Leo Iannacone <l3on@ubuntu.com>
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
# Run autpkgtest and stores output on top of the built
# package in the pool directory.
#
# Can be configured by adding this section to the config file:
#
# [autopkgtest]
# options: [adt-run options]
#

import os
from subprocess import call
from shutil import rmtree


class DebomaticModule_AutoPkgTest:

    def __init__(self):
        self.adt = '/usr/bin/autopkgtest'
        self.options = []
        self.changesfile = None

    def _set_up_testbed(self, args):
        """Performs:
         - check if dsc exists and declares a Testsuite
         - get autopkgtest options from the config
         - set up needed variables and files
        Returns True if test can be executed, False otherwise"""

        # check if dsc exists and it contains the Testsuite field
        autopkgtest_found = False
        for filename in os.listdir(self.resultdir):
            if filename.endswith('.dsc'):
                dsc = os.path.join(self.resultdir, filename)
                with open(dsc, 'r') as fd:
                    for line in fd:
                        if line.find('Testsuite: autopkgtest') >= 0:
                            autopkgtest_found = True
                            break
            if filename.endswith('_%s.changes' % args.architecture):
                self.changesfile = os.path.join(self.resultdir, filename)
        if not self.changesfile or not autopkgtest_found:
            return False

        # get autopkgtest options
        if args.opts.has_section('autopkgtest'):
            if args.opts.has_section('autopkgtest'):
                self.opts = args.opts.get('autopkgtest', 'options').split()

        # set up atd-run output dir
        self.resultdir_adt = os.path.join(self.resultdir, 'adt_out_dir')
        self.summary = 'log_summary'

        return True

    def post_build(self, args):
        if not args.success:
            return
        if not os.access(self.adt, os.X_OK):
            return
        if args.hostarchitecture:
            return

        self.resultdir = os.path.join(args.directory, 'pool', args.package)
        self.output = (os.path.join(self.resultdir, args.package) +
                       '.autopkgtest')
        if not self._set_up_testbed(args):
            return

        output = open(self.output, 'w')

        def write_header(header):
            output.write('┌{:─^70}┐\n'.format('─'))
            output.write('│ {: <69}│\n'.format(header))
            output.write('└{:─^70}┘\n'.format('─'))
            output.flush()

        def append_file(source, new_lines_at_the_end=True):
            if not source.startswith('/'):
                source = os.path.join(self.resultdir_adt, source)
            if os.path.isfile(source):
                with open(source, 'r') as fd:
                    for line in fd:
                        output.write(line)
                    if new_lines_at_the_end:
                        output.write('\n\n')
                output.flush()

        adt = [self.adt, '--apt-upgrade', '--output-dir', self.resultdir_adt,
               '--summary', os.path.join(self.resultdir_adt, self.summary),
               self.changesfile, '--', 'schroot',
               '%s-%s-debomatic' % (args.distribution, args.architecture)]
        if self.options:
            adt.insert(-4, self.options)

        # write the current adt-run command
        write_header('Command')
        output.write(' '.join(adt))
        output.write('\n\n\n')
        output.flush()

        # launch adt-run
        with open(os.devnull, 'w') as fd:
            call(adt, stdout=fd, stderr=fd)

        # build the log properly, first append the summary
        write_header('Tests summary')
        append_file(self.summary)

        # then the log
        write_header('Full log')
        append_file('log')

        # then the others
        all_files = [f for f in os.listdir(self.resultdir_adt) if
                     os.path.isfile(os.path.join(self.resultdir_adt, f)) and
                     f not in ['log', self.summary]]
        for curr_file in all_files:
            write_header('File: %s' % curr_file)
            append_file(curr_file, curr_file != all_files[-1])

        output.close()

        # clean up the system
        if (os.path.isdir(self.resultdir_adt)):
            rmtree(self.resultdir_adt)
