#!/usr/bin/python
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

import cjson
import os
from config import *
from osmstats.helpers import *

def save_jsons(prefix, l, pos, profiles):
    log.info("Saving to JSON")
    f = open(os.path.join(json_path, "%s_%s.json" % (prefix, l[0])), 'w')
    f.write(cjson.encode(l))
    f.close()

    f = open(os.path.join(json_path, '%s_positions.json' % prefix), 'w')
    f.write(cjson.encode(pos))
    f.close()

    # save tags and users lists
    log.info('Saving tags and users lists')
    tags = []
    users = set()
    for key in l[4]:
        for val in l[4][key].keys():
            tags.append('%s=%s' % (key, val))
            users.update(l[4][key][val].keys())

    users = list(users)
    f = open(os.path.join(json_path, '%s_tags_users.json' % prefix), 'w')
    f.write(cjson.encode([tags, users]))
    f.close()

    # save profile data
    users = set()
    for l in [x.keys() for x in profiles]:
        users.update(l)

    # clean up old profiles
    map(os.remove, glob(os.path.join(profiles_path, '%s_*.json' % prefix)))

    for user in users:
        f = open(os.path.join(profiles_path, '%s_%s.json' % (prefix, sanitize(user).replace(' ', '_'))), 'w')
        f.write(cjson.encode([profiles[0][user], profiles[1][user]]))
        f.close()
