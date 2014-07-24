# Deb-o-Matic - AutoPkgTest module
#
# Copyright (C) 2014 Leo Iannacone
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
# logging: [True|False] # enable builder log into the logs directory
#

import os
from subprocess import call
from time import strftime
from shutil import rmtree
from tempfile import NamedTemporaryFile


class DebomaticModule_AutoPkgTest:

    def __init__(self):
        self.options = []
        self.logging = False
        self.dsc = None
        self.gpghome = '/var/cache/debomatic/autopkgtest'

    def _set_up_commons(self, args):
        """Set up common variables for pre and post build hooks"""
        # the package result dir
        self.resultdir = os.path.join(args['directory'],
                                      'pool',
                                      args['package'])
        # output is the final output file log
        self.output = os.path.join(self.resultdir,
                                   args['package']) + '.autopkgtest'

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
                self.dsc = os.path.join(self.resultdir, filename)
                with open(self.dsc, 'r') as fd:
                    for line in fd:
                        if line.find('Testsuite: autopkgtest') >= 0:
                            autopkgtest_found = True
                            break
                break
        if not self.dsc or not autopkgtest_found:
            return False

        # get autopkgtest options
        if args['opts'].has_section('autopkgtest'):
            def get_option(o):
                if args['opts'].has_option('autopkgtest', o):
                    return args['opts'].get('autopkgtest', o).strip()
                return ''
            self.options = get_option('options').split()
            self.logging = get_option('logging').lower() == 'true'
            # gpghome is where adt has its own gpg and it is also used
            # as tmp directory to put the scripts
            gpghome = get_option('gpghome')
            if gpghome:
                self.gpghome = gpghome

        # set up atd-run output dir
        self.resultdir_adt = os.path.join(self.resultdir, 'adt_out_dir')

        # summary is where the test summary is stored, relative to resultdir_adt
        self.summary = 'log_summary'

        # script is the main script launched through the builder, a tmp file
        tmpfd = NamedTemporaryFile(dir=self.gpghome, delete=False)
        tmpfd.close()
        self.script = tmpfd.name
        self._make_script()
        return True

    def _make_script(self):
        """Makes a bash script to being easily called through the builder.
        The script installs autopkgtest and then run adt-run."""
        adt = ['adt-run']
        adt += ('--gnupg-home', self.gpghome)
        adt += ('--summary', os.path.join(self.resultdir_adt, self.summary))
        adt += ('--output-dir', self.resultdir_adt)
        adt += self.options
        # add debs
        adt += (os.path.join(self.resultdir, f)
                for f in os.listdir(self.resultdir)
                if f.endswith('.deb'))
        adt += (self.dsc, '---', 'null')
        self.adt = ' '.join(adt)

        content = ["#!/bin/bash"]
        content.append('apt-get install -y autopkgtest')
        content.append(self.adt)

        if not os.path.isdir(self.gpghome):
            os.makedirs(self.gpghome)
        with open(self.script, 'w') as fd:
            fd.write('\n'.join(content))

    def _finish(self):
        """Clean up the system"""
        if os.path.isfile(self.script):
            os.remove(self.script)
        if (os.path.isdir(self.resultdir_adt)):
            rmtree(self.resultdir_adt)

    def pre_build(self, args):
        # remove previous .autopkgtest file
        self._set_up_commons(args)
        if os.path.isfile(self.output):
            os.remove(self.output)

    def post_build(self, args):
        if not args['success']:
            return

        self._set_up_commons(args)
        if not self._set_up_testbed(args):
            return

        # the output file descriptor
        output = open(self.output, 'w')

        def write_header(header, symbol='~'):
            header = '{}{: ^70}{}'.format(symbol, header, symbol)
            output.write(symbol * len(header) + '\n')
            output.write(header + '\n')
            output.write(symbol * len(header) + '\n')
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

        # write the current adt-run command
        write_header('Command')
        output.write(self.adt)
        output.write('\n\n\n')
        output.flush()

        # call the builder and run adt-run
        builder = args['opts'].get('default', 'builder')
        base = '--basepath' if builder == 'cowbuilder' else '--basetgz'
        with open(os.devnull, 'w') as fd:
            cmd = [builder, '--execute', '--override-config']
            cmd += (base, '%s/%s' % (args['directory'], args['distribution']))
            cmd += ('--architecture', args['architecture'])
            cmd += ('--buildplace', '%s/build' % args['directory'])
            cmd += ('--aptcache', '%s/aptcache' % args['directory'])
            cmd += ('--hookdir', args['opts'].get('default', 'pbuilderhooks'))
            cmd += ('--configfile', args['cfg'])
            cmd += ('--bindmount', self.gpghome)
            cmd += ('--bindmount', self.resultdir)

            if self.logging:
                cmd += ('--logfile', '%s/logs/%s.%s' % (args['directory'],
                        'autopkgtest',
                        strftime('%Y%m%d_%H%M%S')))

            cmd += ('--', '/bin/bash', self.script)

            call(cmd, stdout=fd, stderr=fd)

        # build the log properly, first append the summary
        write_header('Tests summary')
        append_file(self.summary)

        # then the log
        write_header('Full log')
        append_file('log')

        # then the others
        all_files = [f for f in os.listdir(self.resultdir_adt) if
                     os.path.isfile(os.path.join(self.resultdir_adt, f))
                     and not f in ['log', self.summary]]
        for curr_file in all_files:
            write_header('File: %s' % curr_file)
            append_file(curr_file, curr_file != all_files[-1])

        output.close()
        self._finish()
