# Deb-o-Matic - Lintian module
#
# Copyright (C) 2008 David Futcher
# Copyright (C) 2008 Luca Falavigna
#
# Authors: David Futcher <bobbo@ubuntu.com>
#          Luca Falavigna <dktrkranz@ubuntu.com>
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
#
# Prints build start and finish times into a file in the build directory

import os
import stat
from datetime import datetime

class DebomaticModule_DateStamp:

    def __init__(self):
        self.date_file = ""
        
    def pre_build(self, args):    
        self.date_file = "%(directory)s/result/%(package)s/%(package)s.datestamp" % args
        fd = os.open(self.date_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        os.write(fd, 'Build started at %s\n' % datetime.now().strftime("%A, %d. %B %Y %H:%M"))
        os.close(fd)
                
    def post_build(self, args):    
        fd = os.open(self.date_file, os.O_WRONLY | os.O_APPEND)
        os.write(fd, 'Build finished at %s\n' % datetime.now().strftime("%A, %d. %B %Y %H:%M"))
        os.close(fd)
