# Deb-o-Matic
#
# Copyright (C) 2007-2025 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
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

import os
from glob import glob
from logging import debug, error, info
from re import findall
from signal import SIGTERM

from Debomatic import dom
from .build import Build
from .exceptions import DebomaticError
from .gpg import GPG


class Command():

    def __init__(self, commandfile):
        self.incoming = dom.opts.get('debomatic', 'incoming')
        self.cmdfile = os.path.join(self.incoming, commandfile)
        self._process_command()

    def _process_command(self):
        info(_('Processing %s') % os.path.basename(self.cmdfile))
        try:
            with GPG(self.cmdfile) as gpg:
                try:
                    self.uploader = gpg.check()
                except DebomaticError:
                    os.remove(self.cmdfile)
                    error(gpg.error())
                    return
        except IOError:
            return
        with open(self.cmdfile, 'r') as fd:
            cmd = fd.read()
        os.remove(self.cmdfile)
        cmd_nmu = findall(r'\s?binnmu\s+(\S+_\S+) (\S+) (\d+) "(.*)" (.*)',
                          cmd)
        cmd_builddep = findall(r'\s?builddep\s+(\S+_\S+) (\S+) (.*)', cmd)
        cmd_kill = findall(r'\s?kill\s+(\S+_\S+) (\S+)', cmd)
        cmd_porter = findall(r'\s?porter\s+(\S+_\S+) (\S+) (.*)', cmd)
        cmd_rebuild = findall(r'\s?rebuild\s+(\S+_\S+) (\S+) ?(\S*)', cmd)
        cmd_rm = findall(r'\s?rm\s+(.*)', cmd)
        if cmd_nmu:
            self._process_binnmu(cmd_nmu)
        if cmd_builddep:
            self._process_builddep(cmd_builddep)
        if cmd_kill:
            self._process_kill(cmd_kill)
        if cmd_porter:
            self._process_porter(cmd_porter)
        if cmd_rebuild:
            self._process_rebuild(cmd_rebuild)
        if cmd_rm:
            self._process_rm(cmd_rm)

    def _process_binnmu(self, packages):
        debug(_('Performing a binNMU build'))
        for _package in packages:
            package = _package[0].split('_')
            distribution = _package[1]
            binnmu = _package[2]
            changelog = _package[3]
            maintainer = _package[4]
            b = Build(package=package, distribution=distribution,
                      binnmu=(binnmu, changelog), maintainer=maintainer,
                      uploader=self.uploader)
            if dom.pool.schedule(b.run):
                debug(_('Thread for %s scheduled') % '_'.join(package))

    def _process_builddep(self, packages):
        debug(_('Performing a package rebuild with extra dependencies'))
        for _package in packages:
            package = _package[0].split('_')
            distribution = _package[1]
            extrabd = [x.strip() for x in _package[2].split(',')]
            b = Build(package=package, distribution=distribution,
                      extrabd=extrabd, uploader=self.uploader)
            if dom.pool.schedule(b.run):
                debug(_('Thread for %s scheduled') % '_'.join(package))

    def _process_kill(self, builds):
        debug(_('Killing build task'))
        for _build in builds:
            package, version = _build[0].split('_')
            distribution = _build[1]
            for task in dom.buildqueue:
                if task.match(package, version, distribution):
                    pid = task.get_pid()
                    if pid:
                        os.kill(pid, SIGTERM)
                        debug(_('Build killed for %(package)s_'
                                '%(version)s in %(dist)s') %
                              {'package': package, 'version': version,
                               'distribution': distribution})

    def _process_porter(self, packages):
        debug(_('Performing a porter build'))
        for _package in packages:
            package = _package[0].split('_')
            distribution = _package[1]
            maintainer = _package[2]
            b = Build(package=package, distribution=distribution,
                      maintainer=maintainer, uploader=self.uploader)
            if dom.pool.schedule(b.run):
                debug(_('Thread for %s scheduled') % '_'.join(package))

    def _process_rebuild(self, packages):
        debug(_('Performing a package rebuild'))
        for _package in packages:
            package = _package[0].split('_')
            distribution = _package[1]
            origin = _package[2] if _package[2] else distribution
            b = Build(package=package, distribution=distribution,
                      origin=origin, uploader=self.uploader)
            if dom.pool.schedule(b.run):
                debug(_('Thread for %s scheduled') % '_'.join(package))

    def _process_rm(self, filesets):
        debug(_('Removing files'))
        for files in filesets:
            for pattern in files.split():
                pattern = os.path.basename(pattern)
                for absfile in glob(os.path.join(self.incoming, pattern)):
                    debug(_('Removing %s') % absfile)
                    os.remove(absfile)
