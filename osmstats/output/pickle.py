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

import os
import cPickle as pickle
from collections import defaultdict

from config import *
from osmstats.helpers import *

def make_pickles(prefix, date, nodes, ways, rels, tags, positions):
    log.info("Rendering HTML")

    log.info("Sorting users")
    sortedtags = defaultdict(dict)
    splittags = defaultdict(dict)
    for key in tags:
        log.debug("Sorting users for key %s" % key)
        for val in tags[key]:
            sortedtags[key][val] = mysort(tags[key][val])
            splittags[key][val] = mysort(tags[key][val], split=maxsplit)

    primpos = positions_changed(positions[0])
    tagpos = positions_changed(positions[1])
    for t in [(None, sortedtags), (maxsplit, splittags)]:
        if not t[0]:
            # i.e. if t[0] is None, i.e. we're doing the full tags
            for i in [('Nodes', nodes), ('Ways', ways), ('Relations', rels)]:
                log.debug("Rendering full-page for %s (%s)" % (i[0].lower(), date))
                data = dict(
                    date=date,
                    name=i[0],
                    stats=mysort(i[1]),
                    pos=primpos[i[0]],
                    prefix=prefix,
                )
                # table.tmpl
                f = open(os.path.join(pickle_path, '%s_%s_full.pickle' % (prefix, i[0].lower())), "w")
                pickle.dump(data, f, protocol=2)
                f.close()
        else:
            log.debug("Rendering primitives pages (%s)" % date)
            # we're rendering splittags
            data = dict(
                date=date,
                nodes=mysort(nodes, split=t[0]),
                ways=mysort(ways, split=t[0]),
                relations=mysort(rels, split=t[0]),
                prefix=prefix,
                tags=sorted(tags.keys()),
                pos=primpos,
                split=t[0],
            )
            # statistiche.tmpl
            f = open(os.path.join(pickle_path, '%s_stats.pickle' % prefix), "w")
            pickle.dump(data, f, protocol=2)
            f.close()


        for key in sorted(t[1].keys()):
            if not t[0]:
                for val in t[1][key]:
                    valname = val
                    if "|" in val:
                        valname = val.split('|')[0]
                    log.debug("Rendering full-page for %s=%s (%s)" % (key, valname, date))
                    data = dict(
                        date=date,
                        name="%s=%s" % (key, val),
                        stats=t[1][key][val],
                        pos=tagpos[key][val],
                        prefix=prefix,
                    )
                    # table.tmpl
                    f = open(os.path.join(pickle_path, '%s_%s=%s_full.pickle' % (prefix, sanitize(key), sanitize(valname))), 'w')
                    pickle.dump(data, f, protocol=2)
                    f.close()
            else:
                log.debug("Rendering pages for %s=* (%s)" % (key, date))
                data = dict(
                    date=date,
                    prefix=prefix,
                    key=key,
                    vals=t[1][key],
                    pos=tagpos[key],
                    split=t[0],
                )
                # key.tmpl
                f = open(os.path.join(pickle_path, '%s_%s.pickle' % (prefix, sanitize(key))), 'w')
                pickle.dump(data, f, protocol=2)
                f.close()
