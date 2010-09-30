#!/usr/bin/env python
# -*- coding: utf-8 -*-

from operator import itemgetter
from collections import defaultdict
from copy import deepcopy

def mysort(d, split=None):
    if not split:
        return sorted(d.items(), key=itemgetter(1), reverse=True)
    else:
        return sorted(d.items(), key=itemgetter(1), reverse=True)[:split]

def myenum(d, split=None):
    enum = {}
    for key in d:
        if not split:
            enum[key] = enumerate(mysort(d[key]))
        else:
            enum[key] = enumerate(mysort(d[key], split=split))
    return enum

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
        if key in ['Nodi', 'Ways', 'Relazioni']:
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
