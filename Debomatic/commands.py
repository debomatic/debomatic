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
from re import findall
from urllib2 import Request, urlopen, HTTPError, URLError

from build import Build
from gpg import GPG


class Command():

    def __init__(self, opts, log, pool, commandfile):
        self.log = log
        self.w = self.log.w
        self.opts = opts
        self.pool = pool
        self.configdir = opts.get('default', 'configdir')
        self.packagedir = opts.get('default', 'packagedir')
        self.cmdfile = os.path.join(self.packagedir, commandfile)

    def process_command(self):
        gpg = GPG(self.opts, self.cmdfile)
        if gpg.gpg:
            if not gpg.sig:
                os.remove(self.cmdfile)
                self.w(gpg.error)
                return
        with open(self.cmdfile, 'r') as fd:
            cmd = fd.read()
        os.remove(self.cmdfile)
        cmd_rm = findall('\s?rm\s+(.*)', cmd)
        cmd_rebuild = findall('\s?rebuild\s+(\S+)_(\S+) (\S+) ?(\S*)', cmd)
        if cmd_rm:
            self.process_rm(cmd_rm)
        if cmd_rebuild:
            self.process_rebuild(cmd_rebuild)

    def process_rm(self, filesets):
        for files in filesets:
            for pattern in files.split():
                pattern = os.path.basename(pattern)
                for absfile in glob(os.path.join(self.packagedir, pattern)):
                    os.remove(absfile)

    def process_rebuild(self, packages):
        parms = {}
        conf = {'mirror': ('[^#]?MIRRORSITE="?(.*[^"])"?\n', 'MIRRORSITE'),
                'components': ('[^#]?COMPONENTS="?(.*[^"])"?\n', 'COMPONENTS')}
        for package in packages:
            dscname = '%s_%s.dsc' % (package[0], package[1])
            target = package[2]
            origin = package[3] if package[3] else package[2]
            originconf = os.path.join(self.configdir, origin)
            try:
                with open(originconf, 'r') as fd:
                    data = fd.read()
            except IOError:
                self.w(_('Unable to open %s') % originconf)
                return
            for elem in conf.keys():
                try:
                    parms[elem] = findall(conf[elem][0], data)[0]
                except IndexError:
                    self.w(_('Please set %(parm)s in %s(conf)s') % \
                           {'parm': conf[elem][0], 'conf': originconf})
                    return
            for component in parms['components'].split():
                request = Request('%s/pool/%s/%s/%s/%s' %
                                  (parms['mirror'], component,
                                   findall('^lib\S|^\S', package[0])[0],
                                           package[0], dscname))
                try:
                    data = urlopen(request).read()
                    break
                except (HTTPError, URLError):
                    data = None
            if data:
                dsc = os.path.join(self.packagedir, dscname)
                with open(dsc, 'w') as fd:
                    fd.write(data)
                b = Build(self.opts, self.log, dsc=dsc,
                          distribution=target, origin=origin)
                self.pool.add_task(b.build)
            else:
                self.w(_('Unable to fetch %s') % \
                       '_'.join((package[0], package[1])))
