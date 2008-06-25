#!/usr/bin/make

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

all: doc
	python setup.py build

doc:
	docbook2x-man docs/debomatic.1.docbook
	docbook2x-man docs/debomatic.conf.5.docbook

install:
	python setup.py install
	gzip debomatic.1
	gzip debomatic.conf.5
	install -m 644 debomatic.1.gz /usr/share/man/man1/debomatic.1.gz
	install -m 644 debomatic.conf.5.gz /usr/share/man/man5/debomatic.conf.5.gz

uninstall:
	rm /usr/bin/debomatic
	rm /usr/lib/python*/site-packages/debomatic*
	rm -fr /usr/lib/python*/site-packages/Debomatic
	rm /usr/share/man/man1/debomatic.1.gz
	rm /usr/share/man/man5/debomatic.conf.5.gz

clean:
	python setup.py clean
	rm -fr build
	rm -f *.1 *.5 *.gz

