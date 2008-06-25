# Deb-o-Matic
#
# Copyright (C) 2007-2008 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
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
from sha import new
from Debomatic import globals
from Debomatic import gpg
from Debomatic import locks
from Debomatic import packages
from Debomatic import parser
from Debomatic import pbuilder

def build_package(directory, configfile, distdir, package, distopts):
    if not locks.buildlock_acquire():
        packages.del_package(package)
        sys.exit(-1)
    dscfile = None
    if not os.path.exists(os.path.join(distdir, 'result')):
        os.mkdir(os.path.join(distdir, 'result'))
    for pkgfile in globals.packagequeue[package]:
            if not dscfile:
                dscfile = findall('(.*\.dsc$)', pkgfile)
    try:
        packageversion = findall('.*/(.*).dsc$', dscfile[0])[0]
    except:
        packageversion = None
    if not os.path.exists(os.path.join(distdir, 'result', packageversion)):
        os.mkdir(os.path.join(distdir, 'result', packageversion))
    os.system('pbuilder build --basetgz %(directory)s/%(distribution)s \
              --distribution %(distribution)s --override-config --pkgname-logfile --configfile %(cfg)s \
              --buildplace %(directory)s/build --buildresult %(directory)s/result/%(package)s \
              --aptcache %(directory)s/aptcache %(dsc)s' % { 'directory': distdir, 'package': packageversion, \
              'cfg': configfile, 'distribution': distopts['distribution'], 'dsc': dscfile[0]})
    packages.rm_package(package)
    locks.buildlock_release()

def check_package(directory, distribution, changes):
    try:
        packagename = findall('(.*_.*)_source.changes', changes)[0]
    except:
        print 'Bad .changes file'
        return
    resultdir = os.path.join(directory, distribution, 'result', packagename)
    lintian = os.path.join(resultdir, packagename) + '.lintian'
    changesfile = None
    for filename in os.listdir(resultdir):
        result = findall('.*.changes', filename)
        if len(result):
            changesfile = os.path.join(resultdir, result[0])
            break
    if changesfile:
        if globals.Options.has_option('checks', 'lintian') and globals.Options.getint('checks', 'lintian'):
            os.system('lintian --allow-root -i -I %s > %s' % (changesfile, lintian))

def build_process():
    directory = globals.Options.get('default', 'packagedir')
    configdir = globals.Options.get('default', 'configdir')
    package = packages.select_package(directory)
    if package:
        distopts = parser.parse_distribution_options(directory, configdir, package)
        try:
            fd = os.open(os.path.join(directory, package), os.O_RDONLY)
        except:
            print 'Unable to open %s' % os.path.join(directory, package)
            packages.del_package(package)
            sys.exit(-1)
        for entry in findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', os.read(fd, os.fstat(fd).st_size)):
            globals.packagequeue[package].append(os.path.join(directory, entry))
        globals.packagequeue[package].append(os.path.join(directory, package))
        os.close(fd)
        if gpg.check_signature(os.path.join(directory, package)) == False:
            packages.rm_package(package)
            sys.exit(-1)
	packages.fetch_missing_files(package, globals.packagequeue[package], directory, distopts)
        distdir = os.path.join(directory, distopts['distribution'])
        if pbuilder.setup_pbuilder(distdir, configdir, distopts) == False:
            packages.del_package(package)
            sys.exit(-1)
        build_package(directory, os.path.join(configdir, distopts['distribution']), distdir, package, distopts)
        check_package(directory, distopts['distribution'], package)

