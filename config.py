#-*- coding: utf-8 -*-

# Copyright © 2010, David Paleino <d.paleino@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os
import logging

basedir = os.path.dirname(__file__)

pickle_path = 'pickle'
html_path = 'html'
json_path = 'json'
po_path = 'po'
locale_path = os.path.join(po_path, 'locales')
profiles_path = os.path.join(json_path, 'profiles')
templates_path = 'views'
maxsplit = 100

graphs_path = 'graphs'
graphs_cache = os.path.join(graphs_path, 'cached')
graphs_cmddir = os.path.join(graphs_path, 'commands')

default_prefix = 'italy'
default_lang = 'it'

host_ip_addr = ''

### logging
log = logging.getLogger('stats')
log.setLevel(logging.INFO)
logh = logging.StreamHandler()
logh.setLevel(logging.INFO)
logfmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logh.setFormatter(logfmt)
log.addHandler(logh)
