# Deb-o-Matic
#
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
import sys
import threading
from re import findall
from string import lower
from Debomatic import gpg
from Debomatic import locks
from Debomatic import packages
from Debomatic import pbuilder
from Debomatic import Options
from Debomatic import packagequeue
from Debomatic import modules

def build_process():
    directory = Options.get('default', 'packagedir')
    configdir = Options.get('default', 'configdir')
    package = packages.select_package(directory)
    if package:
        distopts = parse_distribution_options(directory, configdir, package)
        try:
            fd = os.open(os.path.join(directory, package), os.O_RDONLY)
        except:
            print 'Unable to open %s' % os.path.join(directory, package)
            packages.del_package(package)
            sys.exit(-1)
        try:
            for entry in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', os.read(fd, os.fstat(fd).st_size)):
                packagequeue[package].append(os.path.join(directory, entry))
        except:
            print 'Bad .changes file'
            sys.exit(-1)
        packagequeue[package].append(os.path.join(directory, package))
        os.close(fd)
        if gpg.check_signature(os.path.join(directory, package)) == False:
            packages.rm_package(package)
            sys.exit(-1)
	packages.fetch_missing_files(package, packagequeue[package], directory, distopts)
        distdir = os.path.join(directory, distopts['distribution'])
        if pbuilder.setup_pbuilder(distdir, configdir, distopts) == False:
            packages.del_package(package)
            sys.exit(-1)
        build_package(directory, os.path.join(configdir, distopts['distribution']), distdir, package, distopts)

def parse_distribution_options(packagedir, configdir, package):
    options = dict()
    try:
        fd = os.open(os.path.join(packagedir, package), os.O_RDONLY)
    except:
        print 'Unable to open %s' % os.path.join(packagedir, package)
        packages.del_package(package)
        sys.exit(-1)
    try:
        distro = findall('Distribution:\s+(\w+)', os.read(fd, os.fstat(fd).st_size))[0]
        options['distribution'] = lower(distro)
    except:
        print 'Bad .changes file'
        packages.del_package(package)
        sys.exit(-1)
    os.close(fd)
    try:
        fd = os.open(os.path.join(configdir,options['distribution']), os.O_RDONLY)
    except:
        print 'Unable to open %s' % os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    conf = os.read(fd, os.fstat(fd).st_size)
    os.close(fd)
    if not len(findall('[^#]?MIRRORSITE="?(.*[^"])"?\n', conf)):
        print 'Please set DISTRIBUTION in %s' % os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    try:
        options['mirror'] = findall('[^#]?MIRRORSITE="?(.*[^"])"?\n', conf)[0]
    except:
        print 'Please set MIRRORSITE in %s' % os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    try:
        options['components'] = findall('[^#]?COMPONENTS="?(.*[^"])"?\n', conf)[0]
    except:
        print 'Please set COMPONENTS in %s' % os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    try:
        options['debootstrap'] = findall('[^#]?DEBOOTSTRAP="?(.*[^"])"?\n', conf)[0]
    except:
        print 'Please set DEBOOTSTRAP in %s' % os.path.join(configdir, options['distribution'])
        packages.del_package(package)
        sys.exit(-1)
    return options

def build_package(directory, configfile, distdir, package, distopts):
    mod_sys = modules.Module()
    if not locks.buildlock_acquire():
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
    except:
        packageversion = None
    if not os.path.exists(os.path.join(distdir, 'pool', packageversion)):
        os.mkdir(os.path.join(distdir, 'pool', packageversion))
    mod_sys.execute_hook('pre_build', { 'directory': distdir, 'package': packageversion, \
              'cfg': configfile, 'distribution': distopts['distribution'], 'dsc': dscfile[0]})
    os.system('pbuilder build --basetgz %(directory)s/%(distribution)s \
              --override-config --configfile %(cfg)s --logfile %(directory)s/pool/%(package)s/%(package)s.buildlog \
              --buildplace %(directory)s/build --buildresult %(directory)s/pool/%(package)s \
              --aptcache %(directory)s/aptcache %(dsc)s >/dev/null 2>&1' % { 'directory': distdir, 'package': packageversion, \
              'cfg': configfile, 'distribution': distopts['distribution'], 'dsc': dscfile[0]})
    mod_sys.execute_hook('post_build', { 'directory': distdir, 'package': packageversion, \
              'cfg': configfile, 'distribution': distopts['distribution'], 'dsc': dscfile[0]})
    packages.rm_package(package)
    locks.buildlock_release()

