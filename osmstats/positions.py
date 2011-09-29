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

import cjson
from collections import defaultdict

from config import *
from osmstats.helpers import *


def calculate_positions(prefix, date, nodes, ways, rels, tags):
    log.info("Calculating positions")
    try:
        primitives_positions, tags_positions = cjson.decode(open('json/%s_positions.json' % prefix).readline())
    except (IOError, cjson.DecodeError):
        primitives_positions = dict()
        tags_positions = dict()

    primitives_positions[date] = defaultdict(list)
    tags_positions[date] = defaultdict(lambda: defaultdict(list))
    primitives_profiles = defaultdict(lambda: defaultdict(tuple))
    tags_profiles = defaultdict(lambda: defaultdict(lambda: defaultdict(tuple)))

    log.debug("Calculating positions for primitives (nodes, ways, relations)")
    for p in [('Nodes', nodes), ('Ways', ways), ('Relations', rels)]:
        for user in enumerate(mysort(p[1])):
            primitives_positions[date][p[0]].append(user[1][0])
            # profiles[<user>]['Nodi'] = (<position>, <number>)
            primitives_profiles[user[1][0]][p[0]] = (user[0] + 1, user[1][1])

    for tag in tags:
        log.debug("Calculating positions for key %s" % tag)
        for val in tags[tag]:
            i = 0
            for user in mysort(tags[tag][val]):
                i += 1
                tags_positions[date][tag][val].append(user[0])
                # profiles[<user>][<key>][<val>] = (<position>, <number>)
                tags_profiles[user[0]][tag][val] = (i, user[1])

    # add positions changed to the profiles
    tmp = positions_changed(primitives_positions)
    for what in tmp:
        # i is 'Ways', 'Nodi', 'Relazioni'
        for user in tmp[what]:
            pos, count = primitives_profiles[user][what]
            # profiles[<user>]['Nodi'] = (<position>, <pos_changed>, <number>)
            primitives_profiles[user][what] = (pos, tmp[what][user], count)

    tmp = positions_changed(tags_positions)
    for key in tmp:
        for val in tmp[key]:
            for user in tmp[key][val]:
                pos, count = tags_profiles[user][key][val]
                # profiles[<user>][key][val] = (<position>, <pos_changed>, <number>)
                tags_profiles[user][key][val] = (pos, tmp[key][val][user], count)


    return ([primitives_positions, tags_positions], [primitives_profiles, tags_profiles])
