# Deb-o-Matic
#
# Copyright (C) 2007-2013 Luca Falavigna
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
from ast import literal_eval
from glob import glob
from re import findall, sub
from urllib2 import Request, urlopen, HTTPError, URLError

from build import Build
from gpg import GPG


class Command():

    def __init__(self, opts, log, pool, commandfile):
        self.log = log
        self.w = self.log.w
        (self.opts, self.rtopts, self.conffile) = opts
        self.pool = pool
        self.configdir = self.opts.get('default', 'configdir')
        self.packagedir = self.opts.get('default', 'packagedir')
        self.cmdfile = os.path.join(self.packagedir, commandfile)

    def fetch_dsc(self):
        parms = {}
        self.data = None
        conf = {'mirror': ('[^#]?MIRRORSITE="?(.*[^"])"?\n', 'MIRRORSITE'),
                'components': ('[^#]?COMPONENTS="?(.*[^"])"?\n', 'COMPONENTS')}
        try:
            with open(self.originconf, 'r') as fd:
                data = fd.read()
        except IOError:
            self.w(_('Unable to open %s') % self.originconf)
            return
        for elem in conf.keys():
            try:
                parms[elem] = findall(conf[elem][0], data)[0]
            except IndexError:
                self.w(_('Please set %(parm)s in %s(conf)s') %
                       {'parm': conf[elem][0], 'conf': self.originconf})
                return
        for component in parms['components'].split():
            request = Request('%s/pool/%s/%s/%s/%s' %
                              (parms['mirror'], component,
                               findall('^lib\S|^\S', self.package)[0],
                               self.package, self.dscname))
            self.w(_('Requesting URL %s' % request.get_full_url()), 3)
            try:
                self.w(_('Downloading missing %s' % self.dscname), 2)
                self.data = urlopen(request).read()
                break
            except (HTTPError, URLError):
                self.w(_('Unable to fetch %s') %
                       '_'.join((self.package, self.version)))

    def mangle_version(self, version):
        self.version = sub('^\d+\:', '', version)

    def map_distribution(self):
        self.rtopts.read(self.conffile)
        if self.rtopts.has_option('runtime', 'mapper'):
            try:
                mapper = literal_eval(self.rtopts.get('runtime', 'mapper'))
            except SyntaxError:
                pass
            else:
                if isinstance(mapper, dict):
                    if self.target in mapper:
                        self.w(_('%(mapped)s mapped as %(mapper)s') %
                               {'mapped': self.target,
                                'mapper': mapper[self.target]}, 2)
                        self.target = mapper[self.target]
                    if self.origin in mapper:
                        self.w(_('%(mapped)s mapped as %(mapper)s') %
                               {'mapped': self.origin,
                                'mapper': mapper[self.origin]}, 2)
                        self.origin = mapper[self.origin]

    def process_command(self):
        self.w(_('Processing %s') % os.path.basename(self.cmdfile))
        gpg = GPG(self.opts, self.cmdfile)
        if gpg.gpg:
            if not gpg.sig:
                os.remove(self.cmdfile)
                self.w(gpg.error)
                return
        with open(self.cmdfile, 'r') as fd:
            cmd = fd.read()
        os.remove(self.cmdfile)
        cmd_builddep = findall('\s?builddep\s+(\S+)_(\S+) (\S+) (.*)', cmd)
        cmd_rm = findall('\s?rm\s+(.*)', cmd)
        cmd_rebuild = findall('\s?rebuild\s+(\S+)_(\S+) (\S+) ?(\S*)', cmd)
        cmd_porter = findall('\s?porter\s+(\S+)_(\S+) (\S+) (.*)', cmd)
        if cmd_builddep:
            self.process_builddep(cmd_builddep)
        if cmd_rm:
            self.process_rm(cmd_rm)
        if cmd_porter:
            self.process_porter(cmd_porter)
        if cmd_rebuild:
            self.process_rebuild(cmd_rebuild)

    def process_builddep(self, packages):
        self.w(_('Performing a package rebuild with extra dependencies'), 2)
        for package in packages:
            self.package = package[0]
            self.mangle_version(package[1])
            self.dscname = '%s_%s.dsc' % (self.package, self.version)
            self.target = package[2]
            self.origin = None
            self.extrabd = package[3]
            self.map_distribution()
            self.originconf = os.path.join(self.configdir, self.target)
            self.fetch_dsc()
            if self.data:
                dsc = os.path.join(self.packagedir, self.dscname)
                with open(dsc, 'w') as fd:
                    fd.write(self.data)
                b = Build((self.opts, self.rtopts, self.conffile), self.log,
                          dsc=dsc, distribution=self.target,
                          extrabd=self.extrabd)
                if self.pool.add_task(b.build, dsc):
                    self.w(_('Thread for %s scheduled' %
                           os.path.basename(dsc)), 3)

    def process_porter(self, packages):
        self.w(_('Performing a porter build'), 2)
        for package in packages:
            self.package = package[0]
            self.mangle_version(package[1])
            self.dscname = '%s_%s.dsc' % (self.package, self.version)
            self.target = package[2]
            self.origin = None
            self.debopts = package[3]
            self.map_distribution()
            self.originconf = os.path.join(self.configdir, self.target)
            self.fetch_dsc()
            if self.data:
                dsc = os.path.join(self.packagedir, self.dscname)
                with open(dsc, 'w') as fd:
                    fd.write(self.data)
                b = Build((self.opts, self.rtopts, self.conffile), self.log,
                          dsc=dsc, distribution=self.target,
                          debopts=self.debopts)
                if self.pool.add_task(b.build, dsc):
                    self.w(_('Thread for %s scheduled' %
                           os.path.basename(dsc)), 3)

    def process_rebuild(self, packages):
        self.w(_('Performing a package rebuild'), 2)
        for package in packages:
            self.package = package[0]
            self.mangle_version(package[1])
            self.dscname = '%s_%s.dsc' % (self.package, self.version)
            self.target = package[2]
            self.origin = package[3] if package[3] else package[2]
            self.map_distribution()
            self.originconf = os.path.join(self.configdir, self.origin)
            self.fetch_dsc()
            if self.data:
                dsc = os.path.join(self.packagedir, self.dscname)
                with open(dsc, 'w') as fd:
                    fd.write(self.data)
                b = Build((self.opts, self.rtopts, self.conffile), self.log,
                          dsc=dsc, distribution=self.target,
                          origin=self.origin)
                if self.pool.add_task(b.build, dsc):
                    self.w(_('Thread for %s scheduled' %
                           os.path.basename(dsc)), 3)

    def process_rm(self, filesets):
        self.w(_('Removing files'), 2)
        for files in filesets:
            for pattern in files.split():
                pattern = os.path.basename(pattern)
                for absfile in glob(os.path.join(self.packagedir, pattern)):
                    self.w(_('Removing %s' % pattern), 2)
                    os.remove(absfile)
