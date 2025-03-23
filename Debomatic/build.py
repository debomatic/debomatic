# Deb-o-Matic
#
# Copyright (C) 2007-2025 Luca Falavigna
# Copyright (C) 2010 Alessio Treglia
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
from ast import literal_eval
from contextlib import contextmanager
from logging import debug, error, info
from re import findall, match, sub
from subprocess import Popen, check_output
from threading import Semaphore
from time import strftime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from Debomatic import dom
from .gpg import GPG
from .modules import Module
from .exceptions import DebomaticError


class BuildTask:

    def __init__(self, build, package, version, distribution, queue):
        self._build = build
        self._package = package
        self._version = version
        self._distribution = distribution
        self._queue = queue
        self._pid = 0

    def __enter__(self):
        for task in self._queue:
            if self.match(task._package, task._version, task._distribution):
                info(_('Build already scheduled for '
                       'package %(package)s_%(version)s in %(dist)s') %
                     {'package': self._package, 'version': self._version,
                      'dist': self._distribution})
                self._skip_removal()
                raise DebomaticError
        self._queue.append(self)
        return self

    def __exit__(self, type, value, tb):
        if self in self._queue:
            self._queue.remove(self)

    def _skip_removal(self):
        for pkgfile in set(self._build.files):
            if os.path.isfile(pkgfile):
                for build in [x._build for x in self._queue
                              if x._build != self]:
                    if pkgfile in build.files:
                        self._build.files.remove(pkgfile)
                        debug(_('Skipping removal of file %s') % pkgfile)

    def get_pid(self):
        return self._pid

    @contextmanager
    def set_pid(self, pid):
        self._pid = pid
        try:
            yield
        finally:
            self._pid = 0

    def match(self, package, version, distribution):
        return (self._package == package and
                self._version == version and
                self._distribution == distribution)


class Build:

    def __init__(self, changesfile=None, package=None, distribution=None,
                 binnmu=None, extrabd=None, maintainer=None, origin=None,
                 uploader=None):
        self.buildtask = None
        self.changesfile = changesfile
        self.package = package
        self.suite = None
        self.distribution = distribution
        self.binnmu = binnmu
        self.extrabd = extrabd
        self.maintainer = maintainer
        self.origin = origin
        self.uploader = uploader
        self.files = set()
        self.incoming = dom.opts.get('debomatic', 'incoming')
        self.hostarchitecture = None
        self.dpr = False

    def _build(self):
        self._parse_distribution()
        if self.distribution in dom.opts.get('distributions', 'blacklist'):
            self._remove_files()
            error(_('Distribution %s is disabled') % self.distribution)
            raise DebomaticError
        if dom.opts.has_section('crossbuild'):
            if dom.opts.getboolean('crossbuild', 'crossbuild'):
                self.hostarchitecture = dom.opts.get('crossbuild',
                                                     'hostarchitecture')
        try:
            if self.changesfile:
                package = os.path.basename(self.changesfile).split('_')[0]
                version = os.path.basename(self.changesfile).split('_')[1]
            else:
                package, version = self.package
            with BuildTask(self, package, version, self.suite,
                           dom.buildqueue) as bt:
                self.buildtask = bt
                self._fetch_files()
                self._setup_chroot()
                self._build_package()
        except DebomaticError:
            self._remove_files()

    def _build_package(self):
        uploader_email = ''
        packageversion = os.path.splitext(os.path.basename(self.dscfile))[0]
        builddir = os.path.join(self.poolpath, 'pool', packageversion)
        os.makedirs(builddir, exist_ok=True)
        if self.uploader:
            uploader_email = self.uploader[1].decode('utf-8')
        architecture = dom.opts.get('debomatic', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        mod = Module()
        mod.args.architecture = architecture
        mod.args.directory = self.poolpath
        mod.args.distribution = self.distribution
        mod.args.dists = dom.dists
        mod.args.dsc = self.dscfile
        mod.args.files = self.files
        mod.args.package = packageversion
        mod.args.uploader = uploader_email
        mod.args.hostarchitecture = self.hostarchitecture
        mod.execute_hook('pre_build')
        info(_('Building %s') % os.path.basename(self.dscfile))
        command = ['sbuild', '--chroot-mode=unshare', '-A', '-s',
                   '-d', self.distribution, f'--arch={architecture}',
                   '-c', f'{self.distribution}-{architecture}-debomatic',
                   '--no-run-lintian', self.dscfile]
        if self.hostarchitecture:
            command.pop(6)
            command.insert(6, '--host=%s' % self.hostarchitecture)
        suite = dom.dists.get(self.distribution, 'suite')
        if self.distribution != suite:
            command.insert(-1, '--build-dep-resolver=aspcud')
            command.insert(-1, ('--aspcud-criteria=-removed,-changed,-new,'
                                '-count(solution,APT-Release:=/%s/)' %
                                self.distribution))
        if self.distribution != self.suite:
            command.insert(-1, '--build-dep-resolver=aspcud')
            command.insert(-1, ('--aspcud-criteria=-removed,-changed,-new,'
                                '-count(solution,APT-Release:=/%s/)' %
                                self.suite))
        if self.extrabd:
            for extrabd in self.extrabd:
                command.insert(-1, '--add-depends=%s' % extrabd)
            command.insert(-1, '--build-dep-resolver=aspcud')
        if self.changesfile:
            with open(self.upload, 'r') as fd:
                data = fd.read()
            for file in findall(r'\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                if '.orig.' in file:
                    command.insert(-1, '--force-orig-source')
                    break
            try:
                command.insert(-1, '--debbuildopt=-v%s~' %
                               findall(r' \S+ \((\S+)\) \S+; ', data)[-1])
            except IndexError:
                pass
            with open(os.path.join(self.incoming, self.changesfile)) as fd:
                data = fd.read()
            for resolver in findall(r'Debomatic-Resolver: (\S+)', data):
                command.insert(-1, '--build-dep-resolver=%s' % resolver)
        if self.binnmu:
            command.insert(-1, '--binNMU=%s' % self.binnmu[0])
            command.insert(-1, '--make-binNMU=%s' % self.binnmu[1])
            command.insert(-1, '--no-arch-all')
            buildlog = '%s+b%s_%s.build' % (packageversion, self.binnmu[0],
                                            architecture)
        else:
            buildlog = '%s_%s.build' % (packageversion, architecture)
        if self.hostarchitecture:
            buildlog = sub(r'(.*_)\S+(\.build)',
                           '\\1%s\\2' % self.hostarchitecture, buildlog)
        if self.maintainer:
            command.remove('-A')
            command.remove('-s')
            command.insert(-1, '--maintainer=%s' % self.maintainer)
        ext = {'.gz': 'gzip', '.bz2': 'bzip2', '.xz': 'xz'}
        for file in self.files:
            if os.path.isfile(file):
                if findall(r'(.*\.debian\..*)', file):
                    try:
                        command.insert(-1, '--debbuildopt=-Z%s' %
                                       ext[os.path.splitext(file)[1]])
                    except IndexError:
                        pass
        for sbuildcommand in self._commands(self.distribution, architecture,
                                            packageversion):
            command.insert(-1, sbuildcommand)
        if self.dpr:
            if dom.opts.get('dpr', 'repository'):
                command.insert(-1, '--extra-repository=%s' %
                               (dom.opts.get('dpr', 'repository') %
                                {'dist': os.path.basename(self.poolpath)}))
        with open(os.devnull, 'w') as fd:
            try:
                buildlink = os.path.join(
                    builddir, f'{packageversion}.buildlog')
                if os.path.exists(buildlink):
                    os.unlink(buildlink)
                os.symlink(buildlog, buildlink)
                process = Popen(command, stdout=fd, stderr=fd, cwd=builddir,
                                start_new_session=True)
                with self.buildtask.set_pid(process.pid):
                    process.wait()
                if process.returncode:
                    info(_("Build of %s failed") %
                         os.path.basename(self.dscfile))
                else:
                    info(_("Build of %s successful") %
                         os.path.basename(self.dscfile))
                    mod.args.success = True
            except OSError:
                error(_('Invocation of sbuild failed'))
        mod.execute_hook('post_build')
        self._remove_files()
        debug(_('Build of %s complete') % os.path.basename(self.dscfile))

    def _commands(self, distribution, architecture, packageversion):
        commands = []
        types = ('pre-build-commands', 'chroot-setup-commands',
                 'build-deps-failed-commands', 'starting-build-commands',
                 'build-failed-commands', 'finished-build-commands',
                 'chroot-cleanup-commands', 'post-build-commands')
        commandsdir = dom.opts.get('chroots', 'commands')
        if os.path.isdir(commandsdir):
            for type in types:
                if os.path.isdir(os.path.join(commandsdir, type)):
                    for command in os.listdir(os.path.join(commandsdir, type)):
                        commandfile = os.path.join(commandsdir, type, command)
                        if os.access(commandfile, os.X_OK):
                            commands.append('--%s=%s %s %s %s' %
                                            (type, commandfile,
                                             packageversion, distribution,
                                             architecture))
        if commands:
            commands.append('--log-external-command-output')
            commands.append('--log-external-command-error')
        return commands

    def _fetch_files(self):

        def _download_files(mirror, component, package, file, filepath):
            request = Request('%s/pool/%s/%s/%s/%s' % (mirror, component,
                              findall(r'^lib\S|^\S', package)[0],
                              package, file))
            try:
                debug(_('Requesting URL %s') % request.get_full_url())
                data = urlopen(request).read()
                with open(filepath, 'wb') as fd:
                    fd.write(data)
            except (HTTPError, URLError):
                pass

        dscfile = None
        components = dom.dists.get(self.origin, 'components').split()
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
            version = sub(r'^\d+\:', '', self.package[1])
            dscfile = '%s_%s.dsc' % (package, version)
            if not dom.dists.has_section(self.origin):
                error(_('Distribution %s not configured') % self.distribution)
                raise DebomaticError
            self.dscfile = os.path.join(self.incoming, dscfile)
            if not os.path.isfile(self.dscfile):
                debug(_('Downloading missing %s') % dscfile)
                for component in components:
                    _download_files(dom.dists.get(self.origin, 'mirror'),
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
        for entry in findall(r'\s\w{32}\s\d+\s(\S+)', data):
            if not os.path.isfile(os.path.join(self.incoming, entry)):
                debug(_('Downloading missing %s') % entry)
                for component in dom.dists.get(self.origin,
                                               'components').split():
                    _download_files(dom.dists.get(self.origin, 'mirror'),
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

    def _lock_chroot(self, chrootname):
        if chrootname not in dom.chroots:
            dom.chroots[chrootname] = Semaphore()
        dom.chroots[chrootname].acquire()

    def _map_distribution(self):
        if dom.opts.has_section('dpr'):
            if dom.opts.getboolean('dpr', 'dpr'):
                self.suite = self.distribution
                if match(r'%s-\S+-\S+' %
                         dom.opts.get('dpr', 'prefix'), self.suite):
                    self.dpr = True
                    self.distribution = '-'.join(
                        self.distribution.split('-')[2:])
                    if self.origin == self.suite:
                        self.origin = self.distribution
        if dom.opts.has_option('distributions', 'mapper'):
            try:
                mapper = literal_eval(dom.opts.get('distributions', 'mapper'))
            except SyntaxError:
                pass
            else:
                if self.distribution in mapper:
                    debug(_('%(mapped)s mapped as %(mapper)s') %
                          {'mapped': self.distribution,
                           'mapper': mapper[self.distribution]})
                    self.distribution = mapper[self.distribution]
                if self.origin and self.origin in mapper:
                    debug(_('%(mapped)s mapped as %(mapper)s') %
                          {'mapped': self.origin,
                           'mapper': mapper[self.origin]})
                    self.origin = mapper[self.origin]

    def _parse_distribution(self):
        if not self.distribution:
            try:
                with open(self.upload, 'r') as fd:
                    data = fd.read()
            except IOError:
                error(_('Unable to open %s') % self.upload)
                raise DebomaticError
            try:
                dist = findall(r'Distribution:\s+(\S+)', data)[0]
                self.distribution = dist.lower()
            except IndexError:
                error(_('Bad .changes file: %s') % self.upload)
                raise DebomaticError
        self.poolpath = os.path.join(self.incoming, self.distribution)
        self._map_distribution()
        if not dom.dists.has_section(self.distribution):
            error(_('Distribution %s not configured') % self.distribution)
            raise DebomaticError
        if self.origin:
            if not dom.dists.has_section(self.origin):
                error(_('Distribution %s not configured') % self.origin)
                raise DebomaticError
        else:
            self.origin = self.distribution
        if not self.suite:
            self.suite = self.distribution

    def _remove_files(self):
        for pkgfile in self.files:
            if os.path.isfile(pkgfile):
                os.remove(pkgfile)
                debug(_('File %s removed') % pkgfile)

    def _setup_chroot(self):
        action = None
        self.buildpath = os.path.join(self.incoming, self.distribution)
        os.makedirs(self.buildpath, exist_ok=True)
        os.makedirs(self.poolpath, exist_ok=True)
        architecture = dom.opts.get('debomatic', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        chrootname = '%s-%s-debomatic' % (self.distribution, architecture)
        self._lock_chroot(chrootname)
        chroot = os.path.expanduser(f'~/.cache/sbuild/{chrootname}.tar.zst')
        if not os.path.isfile(chroot):
            action = 'create'
        mod = Module()
        mod.args.architecture = architecture
        mod.args.action = action
        mod.args.directory = self.buildpath
        mod.args.distribution = self.distribution
        mod.args.dists = dom.dists
        mod.execute_hook('pre_chroot')
        for d in ('logs', 'pool'):
            os.makedirs(os.path.join(self.buildpath, d),
                        exist_ok=True)
        if action:
            logfile = ('%s/logs/%s.%s' %
                       (self.buildpath, self.distribution,
                        strftime('%Y%m%d_%H%M%S')))
            target = dom.dists.get(self.distribution, 'suite')
            with open(logfile, 'w') as fd:
                try:
                    debug(_('Creating chroot %(dist)s-%(arch)s-debomatic') %
                          {'dist': self.distribution, 'arch': architecture})
                    components = ','.join(dom.dists.get(self.distribution,
                                                        'components').split())
                    command = ['mmdebstrap',
                               f'--arch={architecture}',
                               f'--components={components}',
                               target, chroot,
                               dom.dists.get(self.distribution, 'mirror')]
                    if dom.dists.has_option(self.distribution,
                                            'extrapackages'):
                        packages = dom.dists.get(self.distribution,
                                                 'extrapackages').split()
                        command.insert(-3, '--include=%s' % ','.join(packages))
                        packages = '--include=%s' % ','.join(packages)
                    if dom.dists.has_option(self.distribution, 'extramirrors'):
                        extramirrors = dom.dists.get(
                            self.distribution, 'extramirrors')
                        command.append(f'{extramirrors}')
                        if dom.opts.has_section('repository'):
                            keyring = dom.opts.get('repository', 'keyring')
                            keyring_chroot = os.path.dirname(keyring)
                            command.append('--setup-hook=mkdir -p '
                                           f'$1/{keyring}')
                            command.append('--setup-hook=copy-in '
                                           f'{keyring} {keyring_chroot}')
                            command.append('--aptopt='
                                           'Acquire::https::Verify-Peer '
                                           '"false"')
                    process = Popen(command, stdout=fd, stderr=fd)
                    with self.buildtask.set_pid(process.pid):
                        process.wait()
                    if process.returncode:
                        error(_('Failed creating %(dist)s-%(arch)s-debomatic')
                              % {'dist': self.distribution,
                                 'arch': architecture})
                        mod.execute_hook('post_chroot')
                        os.unlink(chroot)
                        self._unlock_chroot(chrootname)
                        raise DebomaticError
                except OSError:
                    error(_('Unable to launch mmdebstrap'))
                    mod.execute_hook('post_chroot')
                    self._unlock_chroot(chrootname)
                    raise DebomaticError
            mod.args.success = True
            mod.execute_hook('post_chroot')
        self._unlock_chroot(chrootname)

    def _unlock_chroot(self, chrootname):
        if chrootname in dom.chroots:
            dom.chroots[chrootname].release()

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
                for entry in findall(r'\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                    entry = os.path.join(self.incoming, entry)
                    self.files.add(entry)
                    debug(_('File %s added') % entry)
            except IndexError:
                error(_('Bad .changes file: %s') % self.upload)
                raise DebomaticError
            try:
                with GPG(self.upload) as gpg:
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
            except (IOError, DebomaticError):
                pass
        else:
            try:
                self._build()
            except DebomaticError:
                self._remove_files()
                error(_('Build of %s failed') % '_'.join(self.package))
