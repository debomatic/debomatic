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
from re import findall
from string import lower
from Debomatic import globals
from Debomatic import packages

defaultoptions = ('packagedir', 'configdir', 'maxbuilds', 'inotify', 'sleep', 'logfile')

def parse_default_options(conffile):
    if not conffile:
        print 'Please specify a configuration file'
        sys.exit(-1)
    if not os.path.exists(conffile):
        print 'Configuration file %s does not exist' % conffile
        sys.exit(-1)
    globals.Options.read(conffile)
    for opt in defaultoptions:
        if not globals.Options.has_option('default', opt) or not globals.Options.get('default', opt):
            print 'Please set "%s" in %s' % (opt, conffile)
            sys.exit(-1)

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
    return options

