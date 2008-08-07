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
from re import findall, DOTALL
from subprocess import Popen, PIPE
from Debomatic import Options

def check_signature(package):
    if Options.getint('gpg', 'gpg'):
        if not Options.has_option('gpg', 'keyring') or not os.path.exists(Options.get('gpg', 'keyring')):
            return False
        gpgresult = Popen(['gpg', '--primary-keyring', Options.get('gpg', 'keyring'), '--verify', package], stderr=PIPE).communicate()[1]
        ID = findall('Good signature from "(.*) <(.*)>"', gpgresult)
        if not len(ID):
            return False
        fd = os.open(package, os.O_RDONLY)
        data = os.read(fd, os.fstat(fd).st_size)
        os.close(fd)
        fd = os.open(package, os.O_WRONLY | os.O_TRUNC)
        os.write(fd, findall('Hash: \S+\n\n(.*)\n\n\-\-\-\-\-BEGIN PGP SIGNATURE\-\-\-\-\-', data, DOTALL)[0])
        os.close(fd)

