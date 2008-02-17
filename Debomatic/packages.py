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
from re import findall, split
from urllib2 import Request, urlopen
from Debomatic import globals

def select_package(directory):
    package = None
    priority = 0
    try:
        filelist = os.listdir(directory)
    except:
        print 'Unable to access directory %s' % directory
        sys.exit(-1)
    for filename in filelist:
        if os.path.splitext(filename)[1] == '.changes':
            if add_package(filename):
                continue
            curprio = get_priority(os.path.join(directory,filename))
            if curprio > priority:
                priority = curprio
                package = filename
    return package

def get_priority(changesfile):
    priority = 0
    priolist = {"low":1, "medium":2, "high":3}
    try:
        fd = os.open(changesfile, os.O_RDONLY)
    except:
        print 'Unable to open %s' % changesfile
        return 0
    urgency =findall('Urgency: (.*)', os.read(fd, os.fstat(fd).st_size))
    priority = priolist[urgency[0]] * 10000000000
    priority += 9999999999 - os.fstat(fd).st_mtime
    os.close(fd)
    return priority

def add_package(package):
    if globals.packagequeue.has_key(package):
        return True
    else:
        globals.packagequeue[package] = list()

def del_package(package):
    try:
        del globals.packagequeue[package]
    except:
        pass

def fetch_missing_files(package, files, packagedir, distopts):
    dscfile = None
    packagename = split('_', package)[0]
    for filename in files:
        if not dscfile:
            dscfile = findall('(.*\.dsc$)', filename)
    fd = os.open(dscfile[0], os.O_RDONLY)
    for entry in findall('\s\w{32}\s\d+\s(\S+)', os.read(fd, os.fstat(fd).st_size)):
        if not os.path.exists(os.path.join(packagedir, entry)):
            for component in split(' ', distopts['components']):
                request = Request('%s/pool/%s/%s/%s/%s' % (distopts['mirror'], component, findall('^lib\S|^\S', packagename)[0], packagename, entry))
                try:
                    data = urlopen(request).read()
                    break
                except:
                    data = None
            if data:
                entryfd = os.open(os.path.join(packagedir, entry), os.O_WRONLY | os.O_CREAT)
                os.write(entryfd, data)
                os.close(entryfd)
                if not (os.path.join(packagedir, entry)) in files:
                    globals.packagequeue[package].append(os.path.join(packagedir, entry))
    os.close(fd)

