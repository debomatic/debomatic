# Deb-o-Matic
#
# Copyright (C) 2010 Alessio Treglia
# Copyright (C) 2007-2009 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
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

import os
import tempfile
import stat
from glob import glob
from re import findall, split
from sys import exit
from subprocess import Popen, PIPE
from Debomatic import gpg
from Debomatic import Options

SUPPORTED_COMMANDS = ('rm|rebuild')

def run_command_rm(uploader, args):
    for files in args:
        for pattern in split(' ', files):
            for absfile in glob(os.path.join(directory, os.path.basename(pattern))):
                os.remove(absfile)

def run_command_rebuild(uploader, args):
    dscfileurl, distribution = args.split()
    curdir_prev = os.path.abspath(os.path.curdir)
    # Create a temporary directory
    tmpdir = tempfile.mkdtemp(prefix='debomatic.')
    os.chdir(tmpdir)
    # Download the package
    retcode = Popen(['dget', '-ud', dscfileurl]).wait()
    if retcode:
        raise Exception("Unable to retrieve the package: dget -ud %s" % dscfileurl)
    # Check
    for dscfile in os.listdir('.'):
        if dscfile.endswith('.dsc'):
            break
    # Extract the package
    pkgsubdir = 'pkg'
    retcode = Popen(['dpkg-source', '-x', dscfile, pkgsubdir]).wait()
    if retcode:
        raise Exception(_("Unable to extract the package: dpkg-source -x %s %s") % (dscfile, pkgsubdir))
    # Generate changes file
    changesfile = dscfile[0:-4] + '_source.changes'
    os.chdir(pkgsubdir)
    fd = os.open(changesfile, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    changesfile_content = Popen([
        'dpkg-genchanges',
        '-S',
        '-sa',
        '-DDistribution=%s' % distribution,
        '-DSigned-By=%s' % uploader,
    ], stdout=PIPE).communicate()[0] # communicate() allows me to avoid use of wait()
    os.write(fd, changesfile_content)
    os.close(fd)
    # TODO: append to the package queue
    os.chdir(curdir_prev)
    retcode = os.system('rm -rf %s' % tempdir)
    if retcode:
        raise Exception(_("Failed to remove %s") % tempdir)

def process_commands():
    directory = Options.get('default', 'packagedir')
    try:
        filelist = os.listdir(directory)
    except:
        print _("Unable to access %s directory") % directory
        exit(-1)
    for filename in filelist:
        cmdfile = os.path.join(directory, filename)
        if os.path.splitext(cmdfile)[1] == '.commands':
            try:
                gpg.check_commands_signature(cmdfile)
            except RuntimeError, error:
                os.remove(cmdfile)
                print error
                continue
            fd = os.open(cmdfile, os.O_RDONLY)
            cmd = os.read(fd, os.fstat(fd).st_size)
            os.close(fd)
            try:
                uploader = findall('Uploader: (.*)', cmd)[0]
            except:
                raise Exception(_("Missing 'Uploader:' field."))
            try:
                cmdline = findall('\s?(%s)\s+(.*)' % SUPPORTED_COMMANDS, cmd)[0]
            except IndexError:
                raise Exception(_('Command not supported.'))
            try:
                exec "run_command_%s(%s, %s)" % (cmdline[0], uploader, cmdline[1])
            except Exception, e:
                raise e # TODO
            # Purge command file
            if os.path.exists(cmdfile):
                os.remove(cmdfile)

