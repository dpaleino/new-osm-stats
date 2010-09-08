#!/usr/bin/env python
# -*- coding: utf-8 -*-

from operator import itemgetter
from collections import defaultdict

def mysort(d):
    return sorted(d.items(), key=itemgetter(1), reverse=True)

def myenum(d):
    enum = {}
    for key in d:
        enum[key] = enumerate(mysort(d[key]))
    return enum

def key_wildcard(key, ret=None):
    if not ret:
        ret = [key]
    if ":" in key:
        partial = key.split(':')[:-1]
        ret.append(':'.join(partial + ['*']))
        key_wildcard(':'.join(partial), ret)
    return ret

def positions_changed(positions):
    ret = defaultdict(dict)
    dates = sorted(positions.keys())
    last = dates[-1:][0]
    try:
        secondlast = dates[-2:-1][0]
    except IndexError:
        secondlast = last
    for key in positions[last]:
        if key in ['Nodi', 'Ways', 'Relazioni']:
            for user in positions[last][key]:
                pos_old = positions[secondlast][key].index(user)
                pos_new = positions[last][key].index(user)
                ret[key][user] = int(pos_old - pos_new)
        else:
            for val in positions[last][key]:
                tmp = defaultdict(dict)
                for user in  positions[last][key][val]:
                    pos_old = positions[secondlast][key][val].index(user)
                    pos_new = positions[last][key][val].index(user)
                    tmp[val][user] = int(pos_old - pos_new)
                ret[key] = tmp
    return ret
