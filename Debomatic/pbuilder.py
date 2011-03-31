# Deb-o-Matic
#
# Copyright (C) 2007-2011 Luca Falavigna
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
from hashlib import sha256
from time import strftime
from urllib2 import urlopen, HTTPError

from Debomatic import locks, Options, log


def setup_pbuilder(directory, configdir, distopts):
    if not os.path.exists(os.path.join(directory)):
        os.mkdir(os.path.join(directory))
    try:
        locks.pbuilderlock_acquire(distopts['distribution'])
    except RuntimeError:
        raise RuntimeError
    try:
        needs_update(directory, distopts['mirror'], distopts['distribution'])
    except RuntimeError as result:
        try:
            prepare_pbuilder(result.args[0], directory, configdir, distopts)
        except RuntimeError as error:
            locks.pbuilderlock_release(distopts['distribution'])
            raise error
        if not os.path.exists(os.path.join(directory, 'gpg')):
            os.mkdir(os.path.join(directory, 'gpg'))
        gpgfile = os.path.join(directory, 'gpg', distopts['distribution'])
        uri = '%s/dists/%s/Release.gpg' % (distopts['mirror'],
                                           distopts['distribution'])
        try:
            remote = urlopen(uri).read()
        except HTTPError:
            locks.pbuilderlock_release(distopts['distribution'])
            raise RuntimeError(_('Unable to fetch %s') % uri)
        with open(gpgfile, 'w') as fd:
            fd.write(remote)
    locks.pbuilderlock_release(distopts['distribution'])


def needs_update(directory, mirror, distribution):
    if not os.path.exists(os.path.join(directory, 'gpg')):
        os.mkdir(os.path.join(directory, 'gpg'))
    gpgfile = os.path.join(directory, 'gpg', distribution)
    if not os.path.exists(gpgfile):
        raise RuntimeError('create')
    if Options.get('default', 'alwaysupdate'):
        if os.path.isfile(Options.get('default', 'alwaysupdate')):
            with open(Options.get('default', 'alwaysupdate'), 'r') as fd:
                for line in fd:
                    if line.rstrip() == distribution:
                        raise RuntimeError('update')
    uri = '%s/dists/%s/Release.gpg' % (mirror, distribution)
    try:
        remote = urlopen(uri).read()
    except HTTPError:
        log.w(_('Unable to fetch %s') % uri)
        raise RuntimeError('update')
    remote_sha = sha256()
    gpgfile_sha = sha256()
    remote_sha.update(remote)
    try:
        with open(gpgfile, 'r') as fd:
            gpgfile_sha.update(fd.read())
    except OSError:
        raise RuntimeError('create')
    if remote_sha.digest() != gpgfile_sha.digest():
        raise RuntimeError('update')


def prepare_pbuilder(cmd, directory, configdir, distopts):
    for d in ('aptcache', 'build', 'logs', 'pool'):
        if not os.path.exists(os.path.join(directory, d)):
            os.mkdir(os.path.join(directory, d))
    for f in ('Packages', 'Release'):
        repo_file = os.path.join(directory, 'pool', f)
        if not os.path.exists(repo_file):
            with open(repo_file, 'w') as fd:
                pass
    if Options.get('default', 'builder') == 'cowbuilder':
        base = '--basepath'
    else:
        base = '--basetgz'
    if (os.system('%(builder)s --%(cmd)s %(basetype)s'
                  ' %(directory)s/%(distribution)s --override-config'
                  ' --buildplace %(directory)s/build'
                  ' --aptcache "%(directory)s/aptcache"'
                  ' --logfile %(directory)s/logs/%(cmd)s.%(now)s'
                  ' --configfile %(cfg)s >/dev/null 2>&1' % \
                  {'builder': Options.get('default', 'builder'), 'cmd': cmd,
                   'directory': directory, 'basetype': base,
                   'distribution': distopts['distribution'],
                   'cfg': os.path.join(configdir, distopts['distribution']),
                   'now': strftime('%Y%m%d_%H%M')})):
        raise RuntimeError(_('%(builder)s %(cmd)s failed') % \
                             {'builder': Options.get('default', 'builder'),
                              'cmd': cmd})
