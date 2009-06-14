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

all: install

install:
	python setup.py install --root=${PREFIX}
	cp -rp etc/* ${PREFIX}/etc
	install -Dm 644 docs/debomatic.1 ${PREFIX}/usr/share/man/man1/debomatic.1
	install -Dm 644 docs/debomatic.conf.5 ${PREFIX}/usr/share/man/man5/debomatic.conf.5

uninstall:
	rm -f ${PREFIX}/usr/bin/debomatic
	rm -fr ${PREFIX}/etc/debomatic ${PREFIX}/etc/default/debomatic ${PREFIX}/etc/init.d/debomatic
	rm -fr ${PREFIX}/usr/lib/python*/*-packages/debomatic*
	rm -fr ${PREFIX}/usr/lib/python*/*-packages/Debomatic
	rm -fr ${PREFIX}/usr/share/debomatic/modules
	rm -f ${PREFIX}/usr/share/man/man1/debomatic.1
	rm -f ${PREFIX}/usr/share/man/man5/debomatic.conf.5

clean:
	python setup.py clean --build-base=${BUILD_BASE}
	rm -fr build

