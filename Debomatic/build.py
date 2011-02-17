# Deb-o-Matic
#
# Copyright (C) 2007-2011 Luca Falavigna
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
import sys
from ConfigParser import NoSectionError
from re import findall

from Debomatic import (gpg, locks, packages, pbuilder,
                       Options, packagequeue, modules)


def build_process():
    directory = Options.get('default', 'packagedir')
    configdir = Options.get('default', 'configdir')
    try:
        blfile = Options.get('default', 'distblacklist')
    except NoSectionError:
        blfile = ''
    distblacklist = []
    if os.path.exists(blfile):
        with open(blfile, 'r') as fd:
            data = fd.read()
        distblacklist = data.split()
    package = packages.select_package(directory)
    if package:
        distopts = parse_distribution_options(directory, configdir, package)
        if distopts['distribution'] in distblacklist:
            print _('Distribution %s is disabled' % distopts['distribution'])
            packages.rm_package(package)
            sys.exit(-1)
        pack = os.path.join(directory, package)
        try:
            with open(pack, 'r') as fd:
                data = fd.read()
        except IOError:
            print _('Unable to open %s') % pack
            packages.del_package(package)
            sys.exit(-1)
        try:
            for entry in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', data):
                packagequeue[package].append(os.path.join(directory, entry))
        except IndexError:
            print _('Bad .changes file: %s') % pack
            sys.exit(-1)
        packagequeue[package].append(pack)
        try:
            uploader = gpg.check_changes_signature(pack)
        except RuntimeError as error:
            packages.rm_package(package)
            print error
            sys.exit(-1)
        packages.fetch_missing_files(package, packagequeue[package],
                                     directory, distopts)
        distdir = os.path.join(directory, distopts['distribution'])
        try:
            pbuilder.setup_pbuilder(distdir, configdir, distopts)
        except RuntimeError as error:
            packages.del_package(package)
            print error
            sys.exit(-1)
        build_package(directory,
                      os.path.join(configdir, distopts['distribution']),
                      distdir, package, uploader, distopts)


def parse_distribution_options(packagedir, configdir, package):
    options = {}
    fld = {'mirror': ('[^#]?MIRRORSITE="?(.*[^"])"?\n', 'MIRRORSITE'),
           'components': ('[^#]?COMPONENTS="?(.*[^"])"?\n', 'COMPONENTS'),
           'debootstrap': ('[^#]?DEBOOTSTRAP="?(.*[^"])"?\n', 'DEBOOTSTRAP')}
    try:
        with open(os.path.join(packagedir, package), 'r') as fd:
            data = fd.read()
    except IOError:
        print _('Unable to open %s') % os.path.join(packagedir, package)
        packages.del_package(package)
        sys.exit(-1)
    try:
        distro = findall('Distribution:\s+(\w+)', data)[0]
        options['distribution'] = distro.lower()
    except IndexError:
        print _('Bad .changes file: %s') % os.path.join(packagedir, package)
        packages.del_package(package)
        sys.exit(-1)
    try:
        with open(os.path.join(configdir, options['distribution'])) as fd:
            conf = fd.read()
    except IOError:
        print _('Unable to open %s') % \
                os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    if not findall('[^#]?DISTRIBUTION="?(.*[^"])"?\n', conf):
        print _('Please set DISTRIBUTION in %s') % \
                os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    for elm in fld.keys():
        try:
            options[elm] = findall(fld[elm][0], conf)[0]
        except IndexError:
            print _('Please set %s in %s') % (fld[elm][0],
                    os.path.join(configdir, options['distribution']))
            packages.del_package(package)
            sys.exit(-1)
    return options


def build_package(directory, configfile, distdir, package, uploader, distopts):
    mod = modules.Module()
    try:
        locks.buildlock_acquire()
    except RuntimeError:
        packages.del_package(package)
        sys.exit(-1)
    dscfile = None
    if not os.path.exists(os.path.join(distdir, 'pool')):
        os.mkdir(os.path.join(distdir, 'pool'))
    for pkgfile in packagequeue[package]:
        if not dscfile:
            dscfile = findall('(.*\.dsc$)', pkgfile)
    try:
        packageversion = findall('.*/(.*).dsc$', dscfile[0])[0]
    except IndexError:
        packageversion = None
    if not os.path.exists(os.path.join(distdir, 'pool', packageversion)):
        os.mkdir(os.path.join(distdir, 'pool', packageversion))
    uploader_email = ''
    if uploader:
        uploader_email = uploader[1]
    mod.execute_hook('pre_build', {'directory': distdir,
                                   'package': packageversion,
                                   'uploader': uploader_email,
                                   'cfg': configfile,
                                   'distribution': distopts['distribution'],
                                   'dsc': dscfile[0]})
    if Options.get('default', 'builder') == 'cowbuilder':
        base = '--basepath'
    else:
        base = '--basetgz'
    os.system('%(builder)s --build %(basetype)s %(directory)s/%(distribution)s'
              ' --override-config  '
              ' --logfile %(directory)s/pool/%(package)s/%(package)s.buildlog'
              ' --buildplace %(directory)s/build'
              ' --buildresult %(directory)s/pool/%(package)s'
              ' --aptcache %(directory)s/aptcache %(debopts)s'
              ' --configfile %(cfg)s %(dsc)s >/dev/null 2>&1'
              % {'builder': Options.get('default', 'builder'),
                 'basetype': base, 'directory': distdir,
                 'package': packageversion, 'cfg': configfile,
                 'distribution': distopts['distribution'],
                 'debopts': packages.get_compression(package),
                 'dsc': dscfile[0]})
    mod.execute_hook('post_build', {'directory': distdir,
                                    'package': packageversion,
                                    'uploader': uploader_email,
                                    'cfg': configfile,
                                    'distribution': distopts['distribution'],
                                    'dsc': dscfile[0]})
    packages.rm_package(package)
    locks.buildlock_release()
