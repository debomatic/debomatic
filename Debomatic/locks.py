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

from threading import Semaphore
from Debomatic import Options
from Debomatic import sema

def buildlock_acquire():
    try:
        return sema.build.acquire(False)
    except:
        sema.build = Semaphore(Options.getint('default', 'maxbuilds'))
        return buildlock_acquire()

def buildlock_release():
    try:
        sema.build.release()
    except:
        pass

def pbuilderlock_acquire(distribution):
    try:
        return sema.pbuilder[distribution].acquire(False)
    except AttributeError:
        sema.pbuilder = dict()
        return pbuilderlock_acquire(distribution)
    except KeyError:
        sema.pbuilder[distribution] = Semaphore()
        return pbuilderlock_acquire(distribution)

def pbuilderlock_release(distribution):
    try:
        sema.pbuilder[distribution].release()
    except:
        pass
