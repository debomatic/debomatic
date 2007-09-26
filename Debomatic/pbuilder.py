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
from time import strftime
from urllib import urlopen
from Debomatic import globals

def setup_pbuilder(directory, configdir, distopts):
    if not os.path.exists(os.path.join(directory)):
        os.mkdir(os.path.join(directory))
    result = needs_update(directory, distopts['mirror'], distopts['distribution'])
    if not globals.sema.update.acquire(False):
        sys.exit(-1)
    if result:
        if threading.activeCount() > 2:
            globals.sema.update.release()
            sys.exit(-1)
        prepare_pbuilder(result, directory, configdir, distopts)
        if not os.path.exists(os.path.join(directory, 'gpg')):
            os.mkdir(os.path.join(directory, 'gpg'))
        gpgfile = os.path.join(directory, 'gpg', distopts['distribution'])
        fd = os.open(gpgfile, os.O_WRONLY | os.O_CREAT, 0664)
        remote = urlopen('%s/dists/%s/Release.gpg' % (distopts['mirror'], distopts['distribution'])).read()
        os.write(fd, remote)
        os.close(fd)
    globals.sema.update.release()

def needs_update(directory, mirror, distribution):
    if not os.path.exists(os.path.join(directory, 'gpg')):
        os.mkdir(os.path.join(directory, 'gpg'))
    gpgfile = os.path.join(directory, 'gpg', distribution)
    if not os.path.exists(gpgfile):
        return 'create'
    try:		
        fd = os.open(gpgfile, os.O_RDONLY)
    except:
        return 'create'
    remote = urlopen('%s/dists/%s/Release.gpg' % (mirror, distribution)).read()
    remote_sha = new(remote)
    gpgfile_sha = new(os.read(fd, os.fstat(fd).st_size))
    os.close(fd)
    if remote_sha.digest() != gpgfile_sha.digest():
        return 'update'

def prepare_pbuilder(cmd, directory, configdir, distopts):
    if not os.path.exists(os.path.join(directory, 'build')):
        os.mkdir(os.path.join(directory, 'build'))
    if not os.path.exists(os.path.join(directory, 'aptcache')):
        os.mkdir(os.path.join(directory, 'aptcache'))
    if not os.path.exists(os.path.join(directory, 'logs')):
        os.mkdir(os.path.join(directory, 'logs'))
    if not os.path.exists(os.path.join(directory, 'work')):
        os.mkdir(os.path.join(directory, 'work'))
    if (os.system('pbuilder %(cmd)s --basetgz %(directory)s/%(distribution)s \
                  --distribution %(distribution)s --override-config \
                  --configfile %(cfg)s --buildplace %(directory)s/build \
                  --aptcache "%(directory)s/aptcache" --logfile %(directory)s/logs/%(cmd)s.%(now)s' \
                  % {'cmd': cmd, 'directory': directory, 'distribution': distopts['distribution'], \
                  'cfg': os.path.join(configdir, distopts['distribution']), 'now': strftime('%Y%m%d_%H%M')})):
        print 'pbuilder (%s) failed' % cmd
        globals.sema.update.release()
        sys.exit(-1)

