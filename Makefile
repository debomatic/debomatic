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

ifeq ($(PREFIX),)
PREFIX=/usr
endif

all: install

install:
	python setup.py install --prefix=${PREFIX}
	cp -rp etc/* /etc
	install -Dm 644 docs/debomatic.1 ${PREFIX}/share/man/man1/debomatic.1
	install -Dm 644 docs/debomatic.conf.5 ${PREFIX}/share/man/man5/debomatic.conf.5

uninstall:
	rm -f ${PREFIX}/bin/debomatic
	rm -fr /etc/debomatic /etc/default/debomatic /etc/init.d/debomatic
	rm -fr ${PREFIX}/lib/python*/*-packages/debomatic*
	rm -fr ${PREFIX}/lib/python*/*-packages/Debomatic
	rm -fr ${PREFIX}/share/debomatic
	rm -f ${PREFIX}/share/man/man1/debomatic.1
	rm -f ${PREFIX}/share/man/man5/debomatic.conf.5

clean:
	python setup.py clean --build-base=${BUILD_BASE}
	rm -fr build

