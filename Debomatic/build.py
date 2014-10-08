# Deb-o-Matic
#
# Copyright (C) 2007-2014 Luca Falavigna
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
from hashlib import sha256
from logging import debug, error, info
from re import findall
from subprocess import call, check_output
from time import strftime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .gpg import GPG
from .modules import Module


class Build:

    def __init__(self, opts, package=None, dsc=None, debopts=None,
                 distribution=None, extrabd=None, origin=None, uploader=None):
        (self.opts, self.rtopts, self.conffile) = opts
        self.package = package
        self.dscfile = dsc
        self.debopts = debopts
        self.distribution = distribution
        self.extrabd = extrabd
        self.origin = origin
        self.cmd = None
        self.distopts = {}
        self.files = set()
        self.packagedir = self.opts.get('default', 'packagedir')
        self.full = False
        self.uploader = uploader

    def build(self):
        if self.full:
            debug(_('Full build routine launched'))
        else:
            debug(_('Simple build routine launched'))
        if self.dscfile:
            self.files.add(self.dscfile)
            debug(_('File %s added') % self.dscfile)
        self.parse_distribution_options()
        if self.distribution in self.runtime_option('distblacklist'):
            self.remove_files()
            error(_('Distribution %s is disabled') % self.distribution)
            raise RuntimeError
        self.fetch_missing_files()
        try:
            self.setup_pbuilder()
        except RuntimeError:
            self.remove_files()
        else:
            self.build_package()

    def build_package(self):
        mod = Module((self.opts, self.rtopts, self.conffile))
        uploader_email = ''
        packageversion = os.path.splitext(os.path.basename(self.dscfile))[0]
        builddir = os.path.join(self.buildpath, 'pool', packageversion)
        info(_('Building %s') % os.path.basename(self.dscfile))
        if not os.path.exists(builddir):
            os.mkdir(builddir)
        if self.uploader:
            uploader_email = self.uploader[1].decode('utf-8')
        builder = self.opts.get('default', 'builder')
        architecture = self.opts.get('default', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        debug(_('Pre-build hooks launched'))
        mod.execute_hook('pre_build', {'cfg': self.configfile,
                                       'directory': self.buildpath,
                                       'distribution': self.distribution,
                                       'architecture': architecture,
                                       'dsc': self.dscfile,
                                       'opts': self.opts,
                                       'package': packageversion,
                                       'uploader': uploader_email})
        debug(_('Pre-build hooks finished'))
        if builder == 'cowbuilder':
            base = '--basepath'
        else:
            base = '--basetgz'
        debopts = ' '.join((self.get_build_options(),
                            self.get_changelog_versions(),
                            self.get_compression(),
                            self.get_orig_tarball()))
        with open(os.devnull, 'w') as fd:
            try:
                debug(_('Launching %s') % builder)
                result = call([builder, '--build', '--override-config',
                               base, '%s/%s' % (self.buildpath,
                                                self.distribution),
                               '--architecture', architecture,
                               '--logfile', '%s/pool/%s/%s.buildlog' %
                               (self.buildpath, packageversion,
                                packageversion),
                               '--buildplace', '%s/build' % self.buildpath,
                               '--buildresult', '%s/pool/%s' %
                               (self.buildpath, packageversion),
                               '--aptcache', '%s/aptcache' % self.buildpath,
                               '--debbuildopts', '%s' % debopts,
                               '--hookdir', self.opts.get('default',
                                                          'pbuilderhooks'),
                               '--extrapackages',
                               '%s' % self.get_extra_builddeps(),
                               '--configfile', self.configfile, self.dscfile],
                              stdout=fd, stderr=fd)
            except OSError:
                error(_('Unable to launch %s') % builder)
                result = -1
        debug(_('Post-build hooks launched'))
        mod.execute_hook('post_build', {'cfg': self.configfile,
                                        'directory': self.buildpath,
                                        'distribution': self.distribution,
                                        'architecture': architecture,
                                        'dsc': self.dscfile,
                                        'opts': self.opts,
                                        'package': packageversion,
                                        'uploader': uploader_email,
                                        'success': result == 0})
        debug(_('Post-build hooks finished'))
        self.remove_files()
        info(_('Build of %s complete') % os.path.basename(self.dscfile))

    def fetch_missing_files(self):
        filename = self.dscfile if self.dscfile else self.package
        packagename = os.path.basename(filename).split('_')[0]
        for filename in self.files:
            if not self.dscfile:
                if filename.endswith('.dsc'):
                    self.dscfile = filename
                    break
        if not self.dscfile:
            self.remove_files()
            error(_('Bad .changes file: %s') % self.package)
            raise RuntimeError
        with open(self.dscfile, 'r') as fd:
            data = fd.read()
        for entry in findall('\s\w{32}\s\d+\s(\S+)', data):
            if not os.path.exists(os.path.join(self.packagedir, entry)):
                for component in self.distopts['ocomponents'].split():
                    request = Request('%s/pool/%s/%s/%s/%s' %
                                      (self.distopts['origin'], component,
                                       findall('^lib\S|^\S', packagename)[0],
                                       packagename, entry))
                    debug(_('Requesting URL %s') % request.get_full_url())
                    try:
                        debug(_('Downloading missing %s') % entry)
                        data = urlopen(request).read()
                        break
                    except (HTTPError, URLError):
                        data = None
                if data:
                    with open(os.path.join(self.packagedir, entry), 'wb') as e:
                        e.write(data)
            if not (os.path.join(self.packagedir, entry)) in self.files:
                entry = os.path.join(self.packagedir, entry)
                self.files.add(entry)
                debug(_('File %s added') % entry)

    def get_build_options(self):
        if self.debopts:
            return '-B -m"%s"' % self.debopts
        else:
            return ''

    def get_changelog_versions(self):
        version = ''
        if self.full:
            with open(os.path.join(self.packagedir, self.package), 'r') as fd:
                data = fd.read()
            try:
                version = '-v%s~' % findall(' \S+ \((\S+)\) \S+; ', data)[-1]
            except IndexError:
                pass
        return version

    def get_compression(self):
        compression = ''
        ext = {'.gz': 'gzip', '.bz2': 'bzip2', '.xz': 'xz'}
        for pkgfile in self.files:
            if os.path.exists(pkgfile):
                if findall('(.*\.debian\..*)', pkgfile):
                    try:
                        compression = ('-Z%s' %
                                       ext[os.path.splitext(pkgfile)[1]])
                    except IndexError:
                        pass
        return compression

    def get_extra_builddeps(self):
        if self.extrabd:
            return self.extrabd
        else:
            return ''

    def get_orig_tarball(self):
        sa = ''
        if self.full:
            with open(self.packagepath, 'r') as fd:
                data = fd.read()
            for file in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                if '.orig.' in file:
                    sa = '-sa'
                    break
        return sa

    def map_distribution(self):
        self.rtopts.read(self.conffile)
        if self.rtopts.has_option('runtime', 'mapper'):
            try:
                mapper = literal_eval(self.rtopts.get('runtime', 'mapper'))
            except SyntaxError:
                pass
            else:
                if isinstance(mapper, dict):
                    if self.distribution in mapper:
                        debug(_('%(mapped)s mapped as %(mapper)s') %
                              {'mapped': self.distribution,
                               'mapper': mapper[self.distribution]})
                        self.distribution = mapper[self.distribution]

    def needs_update(self):
        distribution = self.distopts['distribution']
        if not os.path.exists(os.path.join(self.buildpath, 'gpg')):
            os.mkdir(os.path.join(self.buildpath, 'gpg'))
        gpgfile = os.path.join(self.buildpath, 'gpg', distribution)
        if not os.path.exists(gpgfile):
            self.cmd = 'create'
            debug(_('%s chroot must be created') % distribution)
            return
        if self.distribution in self.runtime_option('alwaysupdate'):
            self.cmd = 'update'
            debug(_('%s chroot must be updated') % distribution)
            return
        uri = '%s/dists/%s/Release.gpg' % (self.distopts['mirror'],
                                           distribution)
        try:
            remote = urlopen(uri).read()
        except (HTTPError, URLError):
            error(_('Unable to fetch %s') % uri)
            self.cmd = 'update'
            debug(_('%s chroot must be updated') % distribution)
            return
        remote_sha = sha256()
        gpgfile_sha = sha256()
        remote_sha.update(remote)
        try:
            with open(gpgfile, 'r') as fd:
                gpgfile_sha.update(fd.read().encode('utf-8'))
        except OSError:
            self.cmd = 'create'
            debug(_('%s chroot must be created') % distribution)
            return
        if remote_sha.digest() != gpgfile_sha.digest():
            self.cmd = 'update'
            debug(_('%s chroot must be updated') % distribution)

    def parse_distribution_options(self):
        conf = {'components': ('[^#]?COMPONENTS="?(.*[^"])"?\n', 'COMPONENTS'),
                'debootstrap': ('[^#]?DEBOOTSTRAP="?(.*[^"])"?\n',
                                'DEBOOTSTRAP'),
                'distribution': ('[^#]?DISTRIBUTION="?(.*[^"])"?\n',
                                 'DISTRIBUTION'),
                'mirror': ('[^#]?MIRRORSITE="?(.*[^"])"?\n', 'MIRRORSITE'),
                'origin': ('[^#]?MIRRORSITE="?(.*[^"])"?\n', 'MIRRORSITE'),
                'ocomponents': ('[^#]?COMPONENTS="?(.*[^"])"?\n',
                                'COMPONENTS')}
        if self.full:
            try:
                with open(self.packagepath, 'r') as fd:
                    data = fd.read()
            except IOError:
                error(_('Unable to open %s') % self.packagepath)
                raise RuntimeError
            try:
                distro = findall('Distribution:\s+(\S+)', data)[0]
            except IndexError:
                error(_('Bad .changes file: %s') % self.packagepath)
                raise RuntimeError
            self.distribution = distro.lower()
        self.map_distribution()
        self.buildpath = os.path.join(self.packagedir, self.distribution)
        self.configfile = os.path.join(self.opts.get('default', 'configdir'),
                                       self.distribution)
        try:
            with open(self.configfile) as fd:
                data = fd.read()
        except IOError:
            self.remove_files()
            error(_('Unable to open %s') % self.configfile)
            exit(2)
        for elem in conf:
            try:
                if elem not in self.distopts or not self.distopts[elem]:
                    self.distopts[elem] = findall(conf[elem][0], data)[0]
            except IndexError:
                error(_('Please set %(parm)s in %s(conf)s') %
                      {'parm': conf[elem][0], 'conf': conf})
                raise RuntimeError
        if self.origin:
            originconfig = os.path.join(self.opts.get('default', 'configdir'),
                                        self.origin)
            try:
                with open(originconfig) as fd:
                    data = fd.read()
            except IOError:
                error(_('Unable to open %s') % originconfig)
                exit(2)
            for elem in ('origin', 'ocomponents'):
                try:
                    self.distopts[elem] = findall(conf[elem][0], data)[0]
                except IndexError:
                    error(_('Please set %(parm)s in %s(conf)s') %
                          {'parm': conf[elem][0], 'conf': conf})
                    raise RuntimeError
        else:
            self.origin = self.distribution

    def prepare_pbuilder(self):
        builder = self.opts.get('default', 'builder')
        architecture = self.opts.get('default', 'architecture')
        if architecture == 'system':
            b_arch = check_output(['dpkg-architecture', '-qDEB_BUILD_ARCH'])
            architecture = b_arch.strip().decode('utf-8')
        debootstrap = self.opts.get('default', 'debootstrap')
        mod = Module((self.opts, self.rtopts, self.conffile))
        debug(_('Pre-chroot maintenance hooks launched'))
        mod.execute_hook('pre_chroot', {'cfg': self.configfile,
                                        'directory': self.buildpath,
                                        'opts': self.opts,
                                        'distribution': self.distribution,
                                        'architecture': architecture,
                                        'cmd': self.cmd})
        debug(_('Pre-chroot maintenance hooks finished'))
        for d in ('aptcache', 'build', 'logs', 'pool'):
            if not os.path.exists(os.path.join(self.buildpath, d)):
                os.mkdir(os.path.join(self.buildpath, d))
        if builder == 'cowbuilder':
            base = '--basepath'
        else:
            base = '--basetgz'
        with open(os.devnull, 'w') as fd:
            params = {'cfg': self.configfile,
                      'directory': self.buildpath,
                      'opts': self.opts,
                      'distribution': self.distribution,
                      'architecture': architecture,
                      'cmd': self.cmd,
                      'success': True}
            try:
                debug(_('Launching %(builder)s %(cmd)s')
                      % {'builder': builder, 'cmd': self.cmd})
                if call([builder, '--%s' % self.cmd, '--override-config',
                         base, '%s/%s' % (self.buildpath, self.distribution),
                         '--buildplace', '%s/build' % self.buildpath,
                         '--aptcache', '%s/aptcache' % self.buildpath,
                         '--autocleanaptcache',
                         '--architecture', architecture,
                         '--logfile', '%s/logs/%s.%s' %
                         (self.buildpath, self.cmd, strftime('%Y%m%d_%H%M%S')),
                         '--configfile', '%s' % self.configfile,
                         '--debootstrap', debootstrap],
                        stdout=fd, stderr=fd):
                    error(_('%(builder)s %(cmd)s failed') %
                          {'builder': builder, 'cmd': self.cmd})
                    debug(_('Post-chroot maintenance hooks launched'))
                    params['success'] = False
                    mod.execute_hook('post_chroot', params)
                    debug(_('Post-chroot maintenance hooks finished'))
                    raise RuntimeError
            except OSError:
                error(_('Unable to launch %s') % builder)
                debug(_('Post-chroot maintenance hooks launched'))
                params['success'] = False
                mod.execute_hook('post_chroot', params)
                debug(_('Post-chroot maintenance hooks finished'))
                raise RuntimeError
        debug(_('Post-chroot maintenance hooks launched'))
        mod.execute_hook('post_chroot', params)
        debug(_('Post-chroot maintenance hooks finished'))

    def remove_files(self):
        for pkgfile in self.files:
            if os.path.exists(pkgfile):
                os.remove(pkgfile)
                debug(_('File %s removed') % pkgfile)

    def runtime_option(self, option):
        self.rtopts.read(self.conffile)
        if self.rtopts.has_option('runtime', option):
            return self.rtopts.get('runtime', option).split()
        else:
            return ()

    def setup_pbuilder(self):
        if not os.path.exists(os.path.join(self.buildpath)):
            os.mkdir(os.path.join(self.buildpath))
        self.needs_update()
        if self.cmd:
            self.prepare_pbuilder()
            gpgfile = os.path.join(self.buildpath, 'gpg',
                                   self.distopts['distribution'])
            uri = '%s/dists/%s/Release.gpg' % (self.distopts['mirror'],
                                               self.distopts['distribution'])
            try:
                remote = urlopen(uri).read()
            except (HTTPError, URLError):
                error(_('Unable to fetch %s') % uri)
                raise RuntimeError
            with open(gpgfile, 'wb') as fd:
                fd.write(remote)


class FullBuild(Build):

    def run(self):
        self.full = True
        self.packagepath = os.path.join(self.packagedir, self.package)
        self.files.add(self.packagepath)
        debug(_('File %s added') % self.packagepath)
        info(_('Processing %s') % self.package)
        try:
            with open(self.packagepath, 'r') as fd:
                data = fd.read()
        except IOError:
            error(_('Unable to open %s') % self.packagepath)
            raise RuntimeError
        try:
            for entry in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                entry = os.path.join(self.packagedir, entry)
                self.files.add(entry)
                debug(_('File %s added') % entry)
        except IndexError:
            error(_('Bad .changes file: %s') % self.packagepath)
            raise RuntimeError
        try:
            with GPG(self.opts, self.packagepath) as gpg:
                try:
                    self.uploader = gpg.check()
                    self.build()
                except RuntimeError:
                    self.remove_files()
                    error(gpg.error())
                    raise RuntimeError
        except IOError:
            pass
