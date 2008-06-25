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

def daemonize(logfile):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        print 'Fork failed'
        sys.exit(-1)
    os.setsid()
    os.chdir('/')
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        print 'Fork failed'
        sys.exit(-1)
    fin = open('/dev/null', 'r')
    fout = open(logfile, 'a+')
    ferr = open(logfile, 'a+', 0)
    os.dup2(fin.fileno(), sys.stdin.fileno())
    os.dup2(fout.fileno(), sys.stdout.fileno())
    os.dup2(ferr.fileno(), sys.stderr.fileno())

