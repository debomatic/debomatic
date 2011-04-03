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
from re import findall, split
from urllib2 import Request, urlopen, HTTPError, URLError

from Debomatic import acceptedqueue, log, packagequeue


def select_package(directory):
    package = None
    priority = 0
    try:
        filelist = os.listdir(directory)
    except OSError:
        log.e(_('Unable to access %s directory') % directory)
    for filename in filelist:
        if os.path.splitext(filename)[1] == '.changes':
            try:
                add_package(filename)
                curprio = get_priority(os.path.join(directory, filename))
                if curprio > priority:
                    priority = curprio
                    package = filename
            except RuntimeError:
                continue
    return package


def get_priority(changesfile):
    priority = 0
    priolist = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    try:
        with open(changesfile, 'r') as fd:
            urgency = findall('Urgency: (.*)', fd.read())
            priority = priolist[urgency[0]] * 10000000000
            priority += 9999999999 - os.stat(changesfile).st_mtime
    except OSError:
        raise RuntimeError(_('Unable to open %s') % changesfile)
    return priority


def add_package(package):
    if package in packagequeue:
        raise RuntimeError
    else:
        packagequeue[package] = []


def del_package(package):
    try:
        del packagequeue[package]
    except KeyError:
        pass


def rm_package(package):
    for pkgfile in packagequeue[package]:
        if os.path.exists(pkgfile):
            os.remove(pkgfile)
    del_package(package)
    try:
        acceptedqueue.remove(package)
    except ValueError:
        pass


def fetch_missing_files(package, files, packagedir, distopts):
    dscfile = None
    packagename = split('_', package)[0]
    for filename in files:
        if not dscfile:
            dscfile = findall('(.*\.dsc$)', filename)
    with open(dscfile[0], 'r') as fd:
        data = fd.read()
    for entry in findall('\s\w{32}\s\d+\s(\S+)', data):
        if not os.path.exists(os.path.join(packagedir, entry)):
            for component in split(' ', distopts['components']):
                request = Request('%s/pool/%s/%s/%s/%s' % \
                                  (distopts['mirror'], component,
                                   findall('^lib\S|^\S', packagename)[0],
                                   packagename, entry))
                try:
                    data = urlopen(request).read()
                    break
                except (HTTPError, URLError):
                    data = None
            if data:
                with open(os.path.join(packagedir, entry), 'w') as entryfd:
                    entryfd.write(data)
        if not (os.path.join(packagedir, entry)) in files:
            packagequeue[package].append(os.path.join(packagedir, entry))


def get_compression(package):
    ext = {'.gz': 'gzip', '.bz2': 'bzip2', '.lzma': 'lzma', '.xz': 'xz'}
    for pkgfile in packagequeue[package]:
        if os.path.exists(pkgfile):
            if findall('(.*\.debian\..*)', pkgfile):
                try:
                    return '--debbuildopts -Z%s' % \
                            ext[os.path.splitext(pkgfile)[1]]
                except IndexError:
                    pass
    return ''
