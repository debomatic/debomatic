# Deb-o-Matic
#
# Copyright (C) 2007-2012 Luca Falavigna
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
from re import findall, DOTALL
from subprocess import Popen, PIPE
from tempfile import mkstemp


class GPG:

    def __init__(self, opts, filename):
        self.opts = opts
        self.filename = filename
        self.error = None
        self.gpg = self.opts.getint('gpg', 'gpg')
        self.sig = None
        if self.gpg:
            self.check_signature()
            if self.sig:
                self.strip_signature()

    def check_signature(self):
        if self.opts.has_option('gpg', 'keyring'):
            self.keyring = self.opts.get('gpg', 'keyring')
            if not os.path.isfile(self.keyring):
                self.keyring = None
                self.error = _('Keyring not found')
                return
        fd, trustdb = mkstemp()
        os.close(fd)
        os.unlink(trustdb)
        gpgresult = Popen(['gpg', '--homedir', os.path.dirname(self.keyring),
                           '--trustdb-name', trustdb,
                           '--no-default-keyring', '--keyring',
                           self.keyring, '--verify', self.filename],
                          stderr=PIPE).communicate()[1]
        if os.path.isfile(trustdb):
            os.unlink(trustdb)
        signature = findall('Good signature from "(.*) <(.*)>.*"', gpgresult)
        if signature:
            self.sig = signature[0]
        else:
            self.error = _('No valid signatures found')

    def strip_signature(self):
        with open(self.filename, 'r') as fd:
            data = fd.read()
        with open(self.filename, 'w') as fd:
            try:
                fd.write(findall('\n\n(.*?)\n\n?-', data, DOTALL)[0])
            except IndexError:
                pass
