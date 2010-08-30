# Deb-o-Matic
#
# Copyright (C) 2010 Alessio Treglia
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
from re import findall, split
from urllib2 import Request, urlopen
from Debomatic import acceptedqueue
from Debomatic import packagequeue

def select_package(directory):
    package = None
    priority = 0
    try:
        filelist = os.listdir(directory)
    except:
        print _('Unable to access %s directory') % directory
        sys.exit(-1)
    for filename in filelist:
        if os.path.splitext(filename)[1] == '.changes':
            try:
                add_package(filename)
                curprio = get_priority(os.path.join(directory,filename))
                if curprio > priority:
                    priority = curprio
                    package = filename
            except RuntimeError:
                continue
    return package

def get_signer_email(changesfile):
    # Simple email validator - Pay attention! This is *not* RFC2822 compliant
    email_re = '<((?:[^@\\s]+)@(?:(?:[-a-z0-9]+\\.)+[a-z]{2,}))>$'
    try:
        fd = os.open(changesfile, os.O_RDONLY)
    except OSError:
        raise RuntimeError(_('Unable to open %s') % changesfile)
    # Check if the field is properly formed -> i.e. 'Signed-By: Nervous Nerd <email@address.com>'
    signed_by_field = findall('Signed-By: ((?:.*)>)$', os.read(fd, os.fstat(fd).st_size))
    os.close(fd)
    if not signed_by_field:
        return '' # No field 'Signed-By:' was found
    return findall(email_re, signed_by_field[0])[0]

def get_priority(changesfile):
    priority = 0
    priolist = {"low":1, "medium":2, "high":3}
    try:
        fd = os.open(changesfile, os.O_RDONLY)
    except OSError:
        raise RuntimeError(_('Unable to open %s') % changesfile)
    urgency =findall('Urgency: (.*)', os.read(fd, os.fstat(fd).st_size))
    priority = priolist[urgency[0]] * 10000000000
    priority += 9999999999 - os.fstat(fd).st_mtime
    os.close(fd)
    return priority

def add_package(package):
    if packagequeue.has_key(package):
        raise RuntimeError
    else:
        packagequeue[package] = list()

def del_package(package):
    try:
        del packagequeue[package]
    except:
        pass

def rm_package(package):
    for pkgfile in packagequeue[package]:
        if os.path.exists(pkgfile):
            os.remove(pkgfile)
    del_package(package)
    try:
        acceptedqueue.remove(package)
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
            packagequeue[package].append(os.path.join(packagedir, entry))
    os.close(fd)

def get_compression(package):
    ext = {'.gz': 'gzip', '.bz2': 'bzip2', '.lzma': 'lzma', '.xz': 'xz'}
    for pkgfile in packagequeue[package]:
        if os.path.exists(pkgfile):
            if findall('(.*\.debian\..*)', pkgfile):
                try:
                    return "--debbuildopts -Z%s" % ext[os.path.splitext(pkgfile)[1]]
                except:
                    pass
    return ""
