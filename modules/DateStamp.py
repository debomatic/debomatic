# Deb-o-Matic - Lintian module
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2008-2011 Luca Falavigna
#
# Authors: David Futcher <bobbo@ubuntu.com>
#          Luca Falavigna <dktrkranz@debian.org>
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

from datetime import datetime
from time import gmtime, mktime, strftime, time


class DebomaticModule_DateStamp:

    def __init__(self):
        self.ts = ''
        self.begin = ''
        self.end = ''

    def pre_build(self, args):
        self.ts = '%(directory)s/pool/%(package)s/%(package)s.datestamp' % args
        with open(self.ts, 'w') as fd:
            self.begin = gmtime(time())
            now = datetime.now().strftime('%A, %d %B %Y %H:%M')
            fd.write('Build started at %s\n' % now)

    def post_build(self, args):
        with open(self.ts, 'a') as fd:
            self.end = gmtime(time())
            now = datetime.now().strftime('%A, %d %B %Y %H:%M')
            elapsed = strftime('%H:%M:%S',
                               gmtime(mktime(self.end) - mktime(self.begin)))
            fd.write('Build finished at %s\n' % now)
            fd.write('Elapsed time: %s' % elapsed)
