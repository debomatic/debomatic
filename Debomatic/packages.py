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
from re import findall

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

