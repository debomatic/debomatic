# Deb-o-Matic
#
# Copyright (C) 2007 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; only version 2 of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
import sys
import threading
from re import findall
from sha import new
from Debomatic import pbuilder
from Debomatic import globals
from Debomatic import packages
from Debomatic import parser

def build_package(directory, configdir, distdir, packagelist, distopts):
    if not globals.sema.build.acquire(False):
        sys.exit(-1)
    dscfile = None
    if not os.path.exists(os.path.join(distdir, 'result')):
        os.mkdir(os.path.join(distdir, 'result'))
    for package in packagelist:
        if os.path.exists(os.path.join(directory, package)):
            src = os.path.join(directory, package)
            dst = os.path.join(distdir, 'work', package)
            os.renames(src, dst)
            if not dscfile:
                dscfile = findall('(.*\.dsc$)', dst)
    try:
        package = findall('.*/(.*).dsc$', dscfile[0])[0]
    except:
        package = None
    if not os.path.exists(os.path.join(distdir, 'result', package)):
        os.mkdir(os.path.join(distdir, 'result', package))
    os.system('pbuilder build --basetgz %(directory)s/%(distribution)s \
              --distribution %(distribution)s --override-config --pkgname-logfile --configfile %(cfg)s \
              --buildplace %(directory)s/build --buildresult %(directory)s/result/%(package)s \
              --aptcache %(directory)s/aptcache %(dsc)s' % { 'directory': distdir, 'package': package, \
              'cfg': os.path.join(configdir, distopts['distribution']), \
              'distribution': distopts['distribution'], 'dsc': dscfile[0]})
    for package in packagelist:
        if os.path.exists(os.path.join(distdir, 'work', package)):
            os.remove(os.path.join(distdir, 'work', package))
    globals.sema.build.release()

def check_package(directory, distribution, changes):
    try:
        packagename = findall('(.*_.*)_source.changes', changes)[0]
    except:
        print 'Bad .changes file'
        sys.exit(-1)
    resultdir = os.path.join(directory, distribution, 'result', packagename)
    lintian = os.path.join(resultdir, packagename) + '.lintian'
    linda = os.path.join(resultdir, packagename) + '.linda'
    changesfile = None
    for filename in os.listdir(resultdir):
        result = findall('.*.changes', filename)
        if len(result):
            changesfile = os.path.join(resultdir, result[0])
            break
    if changesfile:
        if globals.Options.getint('default', 'lintian'):
            os.system('lintian --allow-root -i -I %s > %s' % (changesfile, lintian))
        if globals.Options.getint('default', 'linda'):
            os.system('linda -q -i %s > %s' % (changesfile, linda))

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
            sys.exit(-1)
        files =findall('\s\w{32}\s\d+\s\S+\s\S+\s(.*)', os.read(fd, os.fstat(fd).st_size))
        files.insert(len(files), package)
        os.close(fd)
        distdir = os.path.join(directory, distopts['distribution'])
        pbuilder.setup_pbuilder(distdir, configdir, distopts)
        build_package(directory, configdir, distdir, files, distopts)
        check_package(directory, distopts['distribution'], package)
