# Deb-o-Matic
#
# Copyright (C) 2007-2010 Luca Falavigna
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
from glob import glob
from re import findall, split
from shutil import rmtree
from sys import exit
from subprocess import call, PIPE
from urllib2 import Request, urlopen
from Debomatic import acceptedqueue, gpg, Options, packagequeue, packages

def process_rm(cmd, packagedir):
    filesets = findall('\s?rm\s+(.*)', cmd)
    for files in filesets:
        for pattern in split(' ', files):
            for absfile in glob(os.path.join(packagedir, os.path.basename(pattern))):
                os.remove(absfile)

def process_rebuild(cmd, packagedir):
    opts = dict()
    packs = findall('\s?rebuild\s+(\S+)_(\S+) (\S+)', cmd)
    for package in packs:
        dscname = '%s_%s.dsc' % (package[0], package[1])
        try:
            fd = os.open(os.path.join(Options.get('default', 'configdir'), \
                         package[2]), os.O_RDONLY)
        except:
            print _('Unable to open %s') \
                % os.path.join(Options.get('default', 'configdir'), package[2])
            return
        data = os.read(fd, os.fstat(fd).st_size)
        try:
            opts['mirror'] = findall('[^#]?MIRRORSITE="?(.*[^"])"?\n', data)[0]
            opts['components'] = findall('[^#]?COMPONENTS="?(.*[^"])"?\n', data)[0]
        except:
             return
        os.close(fd)
        for component in split(' ', opts['components']):
            request = Request('%s/pool/%s/%s/%s/%s' % (opts['mirror'], component, \
                findall('^lib\S|^\S', package[0])[0], package[0], dscname))
            try:
                data = urlopen(request).read()
                break
            except:
                data = None
        if data:
            entryfd = os.open(os.path.join(packagedir, dscname), os.O_WRONLY | os.O_CREAT)
            os.write(entryfd, data)
            os.close(entryfd)
            try:
                p = '%s_%s_source.changes' % (package[0], package[1])
                packages.add_package(p)
                packagequeue[p].append(os.path.join(packagedir, dscname))
            except RuntimeError:
                continue
            packages.fetch_missing_files(p, [os.path.join(packagedir, dscname)], packagedir, opts)
            packages.del_package(p)
            acceptedqueue.append(os.path.join(packagedir, p))
            pdir = os.path.join(packagedir, '.%s_%s' % (package[0], package[1]))
            call(['dpkg-source', '-x', os.path.join(packagedir, dscname), pdir], \
                  stdout=PIPE, stderr=PIPE)
            cwd = os.getcwd()
            os.chdir(pdir)
            fd = os.open(os.path.join(packagedir, p), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            changes = call(['dpkg-genchanges', '-S'], stdout=fd, stderr=PIPE)
            os.close(fd)
            os.chdir(cwd)
            rmtree(pdir)

def process_commands():
    directory = Options.get('default', 'packagedir')
    try:
        filelist = os.listdir(directory)
    except:
        print _('Unable to access %s directory') % directory
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
            os.remove(cmdfile)
            process_rm(cmd, directory)
            process_rebuild(cmd, directory)

