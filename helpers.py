#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
