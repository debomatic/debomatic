# Deb-o-Matic
#
# Copyright (C) 2007-2015 Luca Falavigna
# Copyright (C) 2010 Alessio Treglia
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
from logging import debug, error, info
from re import findall, search, sub
from shutil import copymode, move
from subprocess import call, check_output
from tempfile import NamedTemporaryFile
from time import strftime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .gpg import GPG
from .modules import Module
from .exceptions import DebomaticError


class Build:

    def __init__(self, opts, dists, changesfile=None, package=None,
                 distribution=None, binnmu=None, extrabd=None, maintainer=None,
                 origin=None, uploader=None):
        self.opts = opts
        self.dists = dists
        self.changesfile = changesfile
        self.package = package
        self.distribution = distribution
        self.binnmu = binnmu
        self.extrabd = extrabd
        self.maintainer = maintainer
        self.origin = origin
        self.uploader = uploader
        self.files = set()
        self.incoming = self.opts.get('debomatic', 'incoming')

    def _build(self):
        self._parse_distribution()
        if self.distribution in self.opts.get('distributions', 'blacklist'):
            self._remove_files()
            error(_('Distribution %s is disabled') % self.distribution)
            raise DebomaticError
        try:
            self._fetch_files()
            self._setup_chroot()
        except DebomaticError:
            self._remove_files()
        else:
            self._build_package()

    def _build_package(self):
        uploader_email = ''
        packageversion = os.path.splitext(os.path.basename(self.dscfile))[0]
        builddir = os.path.join(self.buildpath, 'pool', packageversion)
        if not os.path.exists(builddir):
            os.mkdir(builddir)
        if self.uploader:
            uploader_email = self.uploader[1].decode('utf-8')
        architecture = self.opts.get('debomatic', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        mod = Module(self.opts)
        mod.args.architecture = architecture
        mod.args.directory = self.buildpath
        mod.args.distribution = self.distribution
        mod.args.dists = self.dists
        mod.args.dsc = self.dscfile
        mod.args.files = self.files
        mod.args.package = packageversion
        mod.args.uploader = uploader_email
        mod.execute_hook('pre_build')
        info(_('Building %s') % os.path.basename(self.dscfile))
        command = ['sbuild', '-A', '-s', '-d', self.distribution,
                   '--arch=%s' % architecture, '-c',
                   '%s-%s-debomatic' % (self.distribution, architecture),
                   self.dscfile]
        if self.changesfile:
            with open(self.upload, 'r') as fd:
                data = fd.read()
            for file in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                if '.orig.' in file:
                    command.insert(-1, '--force-orig-source')
                    break
            try:
                command.insert(-1, '--debbuildopt=-v%s~' %
                               findall(' \S+ \((\S+)\) \S+; ', data)[-1])
            except IndexError:
                pass
        suite = self.dists.get(self.distribution, 'suite')
        if not (self.distribution == suite or
                self.distribution.startswith(suite)):
            command.insert(-1, '--build-dep-resolver=aptitude')
        if self.binnmu:
            command.insert(-1, '--binNMU=%s' % self.binnmu[0])
            command.insert(-1, '--make-binNMU=%s' % self.binnmu[1])
            buildlog = '%s+b%s_%s.build' % (packageversion, self.binnmu[0],
                                            architecture)
        else:
            buildlog = '%s_%s.build' % (packageversion, architecture)
        if self.extrabd:
            for extrabd in self.extrabd:
                command.insert(-1, '--add-depends=%s' % extrabd)
        if self.maintainer:
            command.remove('-A')
            command.remove('-s')
            command.insert(-1, '--maintainer=%s' % self.maintainer)
        ext = {'.gz': 'gzip', '.bz2': 'bzip2', '.xz': 'xz'}
        for file in self.files:
            if os.path.isfile(file):
                if findall('(.*\.debian\..*)', file):
                    try:
                        command.insert(-1, '--debbuildopt=-Z%s' %
                                       ext[os.path.splitext(file)[1]])
                    except IndexError:
                        pass
        for sbuildcommand in self._commands():
            command.insert(-1, sbuildcommand)
        with open(os.devnull, 'w') as fd:
            try:
                os.chdir(os.path.join(self.buildpath, 'pool', packageversion))
                buildlink = '%s.buildlog' % packageversion
                if os.path.exists(buildlink):
                    os.unlink(buildlink)
                os.symlink(buildlog, buildlink)
                result = call(command, stdout=fd, stderr=fd)
            except OSError:
                error(_('Invoication of sbuild failed'))
                result = -1
        if result == 0:
            mod.args.success = True
        mod.execute_hook('post_build')
        self._remove_files()
        info(_('Build of %s complete') % os.path.basename(self.dscfile))

    def _commands(self):
        commands = []
        types = ('pre-build-commands', 'chroot-setup-commands',
                 'starting-build-commands', 'finished-build-commands',
                 'chroot-cleanup-commands', 'post-build-commands')
        commandsdir = self.opts.get('chroots', 'commands')
        if os.path.isdir(commandsdir):
            for type in types:
                if os.path.isdir(os.path.join(commandsdir, type)):
                    for command in os.listdir(os.path.join(commandsdir, type)):
                        commandfile = os.path.join(commandsdir, type, command)
                        if os.access(commandfile, os.X_OK):
                            commands.append('--%s=%s' % (type, commandfile))
        if commands:
            commands.append('--log-external-command-output')
            commands.append('--log-external-command-error')
        return commands

    def _fetch_files(self):

        def _download_files(mirror, component, package, file, filepath):
            request = Request('%s/pool/%s/%s/%s/%s' % (mirror, component,
                              findall('^lib\S|^\S', package)[0],
                              package, file))
            try:
                debug(_('Requesting URL %s') % request.get_full_url())
                data = urlopen(request).read()
                with open(filepath, 'wb') as fd:
                    fd.write(data)
            except (HTTPError, URLError):
                pass

        dscfile = None
        components = self.dists.get(self.origin, 'components').split()
        if self.changesfile:
            package = os.path.basename(self.changesfile).split('_')[0]
            for filename in self.files:
                if filename.endswith('.dsc'):
                    dscfile = filename
                    self.dscfile = os.path.join(self.incoming, dscfile)
                    break
            if not dscfile:
                self._remove_files()
                error(_('Bad .changes file: %s') % self.changesfile)
                raise DebomaticError
        else:
            package = self.package[0]
            version = sub('^\d+\:', '', self.package[1])
            dscfile = '%s_%s.dsc' % (package, version)
            if not self.dists.has_section(self.origin):
                error(_('Distribution %s not configured') % self.distribution)
                raise DebomaticError
            self.dscfile = os.path.join(self.incoming, dscfile)
            if not os.path.isfile(self.dscfile):
                debug(_('Downloading missing %s') % dscfile)
                for component in components:
                    _download_files(self.dists.get(self.origin, 'mirror'),
                                    component, package,
                                    dscfile, self.dscfile)
                    if os.path.isfile(self.dscfile):
                        break
        if self.dscfile and os.path.isfile(self.dscfile):
            self.files.add(self.dscfile)
            debug(_('File %s added') % self.dscfile)
        else:
            error(_('Unable to fetch %s') % dscfile)
            raise DebomaticError
        with open(self.dscfile, 'r') as fd:
            data = fd.read()
        for entry in findall('\s\w{32}\s\d+\s(\S+)', data):
            if not os.path.isfile(os.path.join(self.incoming, entry)):
                debug(_('Downloading missing %s') % entry)
                for component in self.dists.get(self.origin,
                                                'components').split():
                    _download_files(self.dists.get(self.origin, 'mirror'),
                                    component, package, entry,
                                    os.path.join(self.incoming, entry))
                    if os.path.isfile(os.path.join(self.incoming, entry)):
                        break
            if os.path.isfile(os.path.join(self.incoming, entry)):
                if not (os.path.join(self.incoming, entry)) in self.files:
                    entry = os.path.join(self.incoming, entry)
                    self.files.add(entry)
                    debug(_('File %s added') % entry)
            else:
                error(_('Unable to fetch %s') % entry)
                raise DebomaticError

    def _map_distribution(self):
        if self.opts.has_option('distributions', 'mapper'):
            try:
                mapper = literal_eval(self.opts.get('distributions', 'mapper'))
            except SyntaxError:
                pass
            else:
                if self.distribution in mapper:
                    debug(_('%(mapped)s mapped as %(mapper)s') %
                          {'mapped': self.distribution,
                           'mapper': mapper[self.distribution]})
                    self.distribution = mapper[self.distribution]

    def _parse_distribution(self):
        if not self.distribution:
            try:
                with open(self.upload, 'r') as fd:
                    data = fd.read()
            except IOError:
                error(_('Unable to open %s') % self.upload)
                raise DebomaticError
            try:
                dist = findall('Distribution:\s+(\S+)', data)[0]
                self.distribution = dist.lower()
            except IndexError:
                error(_('Bad .changes file: %s') % self.upload)
                raise DebomaticError
        self._map_distribution()
        if not self.dists.has_section(self.distribution):
            error(_('Distribution %s not configured') % self.distribution)
            raise DebomaticError
        if self.origin:
            if not self.dists.has_section(self.origin):
                error(_('Distribution %s not configured') % self.distribution)
                raise DebomaticError
        else:
            self.origin = self.distribution

    def _remove_files(self):
        for pkgfile in self.files:
            if os.path.isfile(pkgfile):
                os.remove(pkgfile)
                debug(_('File %s removed') % pkgfile)

    def _setup_chroot(self):
        action = None
        self.buildpath = os.path.join(self.incoming, self.distribution)
        if not os.path.exists(os.path.join(self.buildpath)):
            os.mkdir(os.path.join(self.buildpath))
        architecture = self.opts.get('debomatic', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        debootstrap = self.opts.get('debomatic', 'debootstrap')
        with open(os.devnull, 'w') as fd:
            chroots = check_output(['schroot', '-l'], stderr=fd)
        if not search('chroot:%s-%s-debomatic' % (self.distribution,
                                                  architecture),
                      chroots.decode()):
            action = 'create'
        mod = Module(self.opts)
        mod.args.architecture = architecture
        mod.args.action = action
        mod.args.directory = self.buildpath
        mod.args.distribution = self.distribution
        mod.args.dists = self.dists
        mod.execute_hook('pre_chroot')
        for d in ('logs', 'pool'):
            if not os.path.exists(os.path.join(self.buildpath, d)):
                os.mkdir(os.path.join(self.buildpath, d))
        if action:
            profile = self.opts.get('chroots', 'profile')
            if not os.path.isdir(os.path.join('/etc/schroot', profile)):
                error(_('schroot profile %s not found') % profile)
                raise DebomaticError
            logfile = ('%s/logs/%s.%s' %
                       (self.buildpath, self.distribution,
                        strftime('%Y%m%d_%H%M%S')))
            target = self.dists.get(self.distribution, 'suite')
            if target == self.distribution:
                pattern = '%s-%s-debomatic' % (self.distribution, architecture)
            else:
                pattern = '%s-%s-%s-debomatic' % (target, architecture,
                                                  self.distribution)
            with open(logfile, 'w') as fd:
                try:
                    debug(_('Creating chroot %s') % pattern)
                    components = ','.join(self.dists.get(self.distribution,
                                                         'components').split())
                    command = ['sbuild-createchroot',
                               '--arch=%s' % architecture,
                               '--chroot-suffix=-debomatic',
                               '--debootstrap=%s' % debootstrap,
                               '--components=%s' % components, target,
                               os.path.join(self.buildpath, self.distribution),
                               self.dists.get(self.distribution, 'mirror')]
                    if target != self.distribution:
                        command[2] = ('--chroot-suffix=-%s-debomatic' %
                                      self.distribution)
                    if self.dists.has_option(self.distribution,
                                             'extrapackages'):
                        packages = self.dists.get(self.distribution,
                                                  'extrapackages').split()
                        command.insert(-3, '--include=%s' % ','.join(packages))
                        packages = '--include=%s' % ','.join(packages)
                    if call(command, stdout=fd, stderr=fd):
                        error(_('Failed creating %(dist)s-%(arch)s-debomatic')
                              % {'dist': self.distribution,
                                 'arch': architecture})
                        mod.execute_hook('post_chroot')
                        raise DebomaticError
                except OSError:
                    error(_('Unable to launch sbuild-createchroot'))
                    mod.execute_hook('post_chroot')
                    raise DebomaticError
            if self.dists.has_option(self.distribution, 'extramirrors'):
                with open(os.path.join(self.buildpath, self.distribution,
                                       'etc/apt/sources.list'), 'a') as fd:
                    fd.write(self.dists.get(self.distribution, 'extramirrors'))
            chroots = '/etc/schroot/chroot.d'
            for file in os.listdir(chroots):
                if file.startswith(pattern):
                    with NamedTemporaryFile(mode='w+', delete=False) as tmp:
                        with open(os.path.join(chroots, file)) as fd:
                            for line in fd:
                                if line.startswith('['):
                                    tmp.write('[%s-%s-debomatic]\n' %
                                              (self.distribution,
                                               architecture))
                                elif line.startswith('description'):
                                    tmp.write(line.replace(target,
                                              self.distribution))
                                elif line.startswith('profile'):
                                    tmp.write('profile=%s\n' % profile)
                                else:
                                    tmp.write(line)
                        tmp.write('union-type=aufs')
                    copymode(fd.name, tmp.name)
                    move(tmp.name, fd.name)
            mod.args.success = True
            mod.execute_hook('post_chroot')

    def run(self):
        if self.changesfile:
            self.upload = os.path.join(self.incoming, self.changesfile)
            self.files.add(self.upload)
            debug(_('File %s added') % self.upload)
            info(_('Processing %s') % self.changesfile)
            try:
                with open(self.upload, 'r') as fd:
                    data = fd.read()
            except IOError:
                error(_('Unable to open %s') % self.upload)
                raise DebomaticError
            try:
                for entry in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                    entry = os.path.join(self.incoming, entry)
                    self.files.add(entry)
                    debug(_('File %s added') % entry)
            except IndexError:
                error(_('Bad .changes file: %s') % self.upload)
                raise DebomaticError
            try:
                with GPG(self.opts, self.upload) as gpg:
                    try:
                        self.uploader = gpg.check()
                    except DebomaticError:
                        self._remove_files()
                        error(gpg.error())
                        raise DebomaticError
                    try:
                        self._build()
                    except DebomaticError:
                        self._remove_files()
                        error(_('Build of %s failed') % self.changesfile)
            except IOError:
                pass
        else:
            try:
                self._build()
            except DebomaticError:
                self._remove_files()
                error(_('Build of %s failed') % '_'.join(self.package))
