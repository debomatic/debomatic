# Deb-o-Matic
#
# Copyright (C) 2007-2010 Luca Falavigna
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

import Queue
from Debomatic import Options
from Debomatic import buildlock, pbuilderlock

def buildlock_acquire():
    global buildlock
    if not buildlock:
        buildlock = Queue.Queue(Options.getint('default', 'maxbuilds'))
    try:
        buildlock.put_nowait(None)
    except Queue.Full:
        raise RuntimeError

def buildlock_release():
    global buildlock
    if buildlock:
        try:
            buildlock.get_nowait()
        except Queue.Empty:
            pass

def pbuilderlock_acquire(distribution):
    if not pbuilderlock.has_key(distribution):
        pbuilderlock[distribution] = Queue.Queue(1)
    try:
        pbuilderlock[distribution].put_nowait(None)
    except Queue.Full:
        raise RuntimeError

def pbuilderlock_release(distribution):
    if pbuilderlock.has_key(distribution):
        try:
            pbuilderlock[distribution].get_nowait()
        except Queue.Empty:
            pass

