# Deb-o-Matic
#
# Copyright (C) 2007-2011 Luca Falavigna
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
from subprocess import call, PIPE
from urllib2 import Request, urlopen, HTTPError

from Debomatic import acceptedqueue, gpg, log, Options, packagequeue, packages


def process_rm(cmd, packagedir):
    filesets = findall('\s?rm\s+(.*)', cmd)
    for files in filesets:
        for pattern in split(' ', files):
            for absfile in glob(os.path.join(packagedir,
                                             os.path.basename(pattern))):
                os.remove(absfile)


def process_rebuild(cmd, packagedir):
    opts = {}
    packs = findall('\s?rebuild\s+(\S+)_(\S+) (\S+) ?(\S*)', cmd)
    configdir = Options.get('default', 'configdir')
    for package in packs:
        dscname = '%s_%s.dsc' % (package[0], package[1])
        try:
            target = package[3] if package[3] else package[2]
            with open(os.path.join(configdir, target), 'r') as fd:
                data = fd.read()
        except IOError:
            log.w(_('Unable to open %s') % os.path.join(configdir, target))
            return
        try:
            opts['mirror'] = findall('[^#]?MIRRORSITE="?(.*[^"])"?\n', data)[0]
            opts['components'] = findall('[^#]?COMPONENTS="?(.*[^"])"?\n',
                                         data)[0]
        except IndexError:
            return
        for component in split(' ', opts['components']):
            request = Request('%s/pool/%s/%s/%s/%s' % \
                              (opts['mirror'], component,
                               findall('^lib\S|^\S', package[0])[0],
                               package[0], dscname))
            try:
                data = urlopen(request).read()
                break
            except HTTPError:
                data = None
        if data:
            dsc = os.path.join(packagedir, dscname)
            with open(dsc, 'w') as entryfd:
                entryfd.write(data)
            try:
                p = '%s_%s_source.changes' % (package[0], package[1])
                packages.add_package(p)
                packagequeue[p].append(dsc)
            except RuntimeError:
                continue
            packages.fetch_missing_files(p, [dsc], packagedir, opts)
            packages.del_package(p)
            acceptedqueue.append(os.path.join(packagedir, p))
            pdir = os.path.join(packagedir, '.%s_%s' % (package[0],
                                                        package[1]))
            call(['dpkg-source', '-x', dsc, pdir], stdout=PIPE, stderr=PIPE)
            cwd = os.getcwd()
            os.chdir(pdir)
            with open(os.path.join(packagedir, p), 'w') as fd:
                changes = call(['dpkg-genchanges', '-S',
                               '-Ddistribution=%s' % package[2]],
                               stdout=fd, stderr=PIPE)
            os.chdir(cwd)
            rmtree(pdir)


def process_commands():
    directory = Options.get('default', 'packagedir')
    try:
        filelist = os.listdir(directory)
    except OSError:
        log.e(_('Unable to access %s directory') % directory)
    for filename in filelist:
        cmdfile = os.path.join(directory, filename)
        if os.path.splitext(cmdfile)[1] == '.commands':
            try:
                gpg.check_commands_signature(cmdfile)
            except RuntimeError as error:
                os.remove(cmdfile)
                log.w(error)
                continue
            with open(cmdfile, 'r') as fd:
                cmd = fd.read()
            os.remove(cmdfile)
            process_rm(cmd, directory)
            process_rebuild(cmd, directory)
