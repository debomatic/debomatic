# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2022 Luca Falavigna
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
#
# Deb-o-Matic documentation build configuration file


extensions = []
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Deb-o-Matic'
copyright = '2007-2022, Luca Falavigna'
version = '0.25'
release = '0.25'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
html_use_index = True
htmlhelp_basename = 'Deb-o-Maticdoc'
latex_documents = [
    ('index', 'Deb-o-Matic.tex', 'Deb-o-Matic Documentation',
     'Luca Falavigna', 'manual', 'True')]
latex_elements = {
    'classoptions': ',oneside',
    'babel': '\\usepackage[english]{babel}'}
man_pages = [
    ('index', 'deb-o-matic', 'Deb-o-Matic Documentation',
     ['Luca Falavigna'], 1)]
