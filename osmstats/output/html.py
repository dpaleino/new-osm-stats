#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2010-2011, David Paleino <d.paleino@gmail.com>
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

from datetime import datetime
from time import strftime
import os

from config import *

def make_footer():
    today = strftime("%Y-%m-%d %H:%M:%S", datetime.today().timetuple())

    f = open(os.path.join(html_path, 'timestamp.html'), 'w')
    f.write('<i>'+today+'</i>')
    f.close()

    if '~dev' in version:
        versionlink = ''
    else:
        versionlink = version

    f = open(os.path.join(html_path, 'version.html'), 'w')
    f.write('<a href="http://bugs.hanskalabs.net/projects/osm-stats/repository/show?rev=%s">%s</a>' % (versionlink, version))
    f.close()
