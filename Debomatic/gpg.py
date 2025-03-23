# Deb-o-Matic
#
# Copyright (C) 2007-2025 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option), any later version.
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
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
from re import findall, DOTALL
from subprocess import Popen, PIPE

from Debomatic import dom
from .exceptions import DebomaticError


class GPG:

    def __init__(self, file):
        self._file = file
        self._error = None
        if dom.opts.has_option('gpg', 'gpg'):
            self._gpg = dom.opts.getboolean('gpg', 'gpg')
        else:
            self._gpg = False
        self._sig = None

    def __enter__(self):
        self._fd = open(self._file, 'r')
        flock(self._fd, LOCK_EX | LOCK_NB)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        flock(self._fd, LOCK_UN)
        self._fd.close()

    def _check_signature(self):
        if dom.opts.has_option('gpg', 'keyring'):
            self._keyring = dom.opts.get('gpg', 'keyring')
            if not os.path.isfile(self._keyring):
                self._keyring = None
                self._error = _('Keyring not found')
                raise DebomaticError
        gpgresult = Popen(['gpgv', '--keyring', self._keyring, self._file],
                          stderr=PIPE).communicate()[1]
        signature = findall(b'Good signature from "(.*) <(.*)>.*"', gpgresult)
        if signature:
            self._sig = signature[0]
        else:
            self._error = _('No valid signatures found')
            raise DebomaticError

    def _strip_signature(self):
        with open(self._file, 'r') as fd:
            data = fd.read()
        with open(self._file, 'w') as fd:
            try:
                fd.write(findall('\n\n(.*?)\n\n?-', data, DOTALL)[0])
            except IndexError:
                pass

    def check(self):
        if self._gpg:
            self._check_signature()
            if self._sig:
                self._strip_signature()
        return self._sig

    def error(self):
        return self._error
