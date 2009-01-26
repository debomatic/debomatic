#!/usr/bin/make

# Deb-o-Matic
#
# Copyright (C) 2007-2009 Luca Falavigna
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

BUILD_BASE=${PWD}

all: doc
	python setup.py build --build-base=${BUILD_BASE}

doc:
	docbook2x-man docs/debomatic.1.docbook
	docbook2x-man docs/debomatic.conf.5.docbook

install:
	python setup.py install
	install -m 644 debomatic.1 /usr/share/man/man1/debomatic.1
	install -m 644 debomatic.conf.5 /usr/share/man/man5/debomatic.conf.5

uninstall:
	rm /usr/bin/debomatic
	rm /usr/lib/python*/site-packages/debomatic*
	rm -fr /usr/lib/python*/site-packages/Debomatic
	rm /usr/share/man/man1/debomatic.1
	rm /usr/share/man/man5/debomatic.conf.5

clean:
	python setup.py clean --build-base=${BUILD_BASE}
	rm -fr build
	rm -f *.1 *.5

