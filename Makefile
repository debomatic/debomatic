#!/usr/bin/make

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

build:
        python setup.py build

doc:
	docbook2x-man --to-stdout docs/debomatic.1.docbook | gzip -c > docs/debomatic.1.gz
	docbook2x-man --to-stdout docs/debomatic.conf.5.docbook | gzip -c > docs/debomatic.conf.5.gz

install: doc
        python setup.py install
	install -m 644 docs/debomatic.1.gz /usr/share/man/man1/debomatic.1.gz
	install -m 644 docs/debomatic.conf.5.gz /usr/share/man/man5/debomatic.conf.5.gz

uninstall:
        rm /usr/bin/debomatic
        rm /usr/lib/python*/site-packages/debomatic*
	rm /usr/share/man/man1/debomatic.1.gz
	rm /usr/share/man/man5/debomatic.conf.5.gz

clean:
        python setup.py clean
