#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from operator import itemgetter
from collections import defaultdict
from copy import deepcopy

import config

def mysort(d, split=None):
    if not split:
        return sorted(d.items(), key=itemgetter(1), reverse=True)
    else:
        return sorted(d.items(), key=itemgetter(1), reverse=True)[:split]

def key_wildcard(key, ret=None):
    if not ret:
        ret = [key]
    if key[-2:] != ':*':
        ret.append(key+':*')
    if ":" in key:
        partial = key.split(':')[:-1]
        ret.append(':'.join(partial + ['*']))
        key_wildcard(':'.join(partial), ret)
    return set(ret)

def check_tuple(t, values):
    for v in t:
        if v in values:
            return true
    return false

def get_last_dates(positions):
    dates = sorted(positions.keys())
    last = dates[-1:][0]
    try:
        secondlast = dates[-2:-1][0]
    except IndexError:
        secondlast = last
    return secondlast, last

def positions_changed(positions):
#    ret = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    ret = defaultdict(dict)
    secondlast, last = get_last_dates(positions)

    for key in positions[last]:
        if key in ['Nodes', 'Ways', 'Relations']:
            for user in positions[last][key]:
                pos_new = positions[last][key].index(user)
                try:
                    pos_old = positions[secondlast][key].index(user)
                except ValueError:
                    # a new user joined us. Yay! \o/
                    pos_old = pos_new
                ret[key][user] = int(pos_old - pos_new)
        else:
            # FIXME: this will be useful when supporting intermediate
            # renderings
#            # Try to sanitize keys
#            # TODO: this should REALLY be fixed.
#            oldkeys = positions[secondlast][key].keys()
#            newkeys = positions[last][key].keys()
#            keyscopy = deepcopy(newkeys)
#
#            for t in [(oldkeys, newkeys), (keyscopy, oldkeys)]:
#                for v in t[0]:
#                    try:
#                        t[1].remove(v)
#                    except ValueError:
#                        pass
#            if oldkeys != newkeys:
#                # oldkeys contains keys present in positions[secondlast] but not in [last]
#                # newkeys contains keys present in positions[last] but not in [secondlast]
#                print repr(oldkeys), repr(newkeys), repr(keyscopy)
#                pass

            for val in positions[last][key]:
                tmp = defaultdict(int)
                for user in positions[last][key][val]:
                    pos_new = positions[last][key][val].index(user)
                    try:
                        pos_old = positions[secondlast][key][val].index(user)
                    except (KeyError, ValueError):
                        # maybe some new tag was added since the last run, or
                        # a new user joined the clan!
                        pos_old = pos_new
                    tmp[user] = int(pos_old - pos_new)
                ret[key][val] = tmp
    return ret

def sanitize(name):
    name = name.replace('*', '')
    name = name.replace(':', '-')
    name = name.replace('/', '-')
    return name

def get_prefix(request):
    if request.GET.get('prefix'):
        return str(sanitize(request.GET['prefix']))
    else:
        return config.default_prefix
