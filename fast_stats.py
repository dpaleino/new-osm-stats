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

from collections import defaultdict
import cjson
import os
from glob import glob

from config import *
from makepickle import make_pickles

from osmstats.backends.osmxml import parse
from osmstats.helpers import *

### code

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

def make_footer():
    from datetime import datetime
    from time import strftime
    today = strftime("%Y-%m-%d %H:%M:%S", datetime.today().timetuple())

    f = open(os.path.join(html_path, 'timestamp.html'), 'w')
    f.write('<i>'+today+'</i>')
    f.close()

    if '~dev' in config.version:
        versionlink = ''
    else:
        versionlink = config.version

    f = open(os.path.join(html_path, 'version.html'), 'w')
    f.write('<a href="http://bugs.hanskalabs.net/projects/osm-stats/repository/show?rev=%s">%s</a>' % (versionlink, config.version))
    f.close()

def main(prefix, date, filename):
    make_footer()
    nodes, ways, rels, tags = parse(filename)
    positions, profiles = calculate_positions(prefix, date, nodes, ways, rels, tags)
    save_jsons(prefix, [date, nodes, ways, rels, tags], positions, profiles)

    # render the last date, we don't support rendering intermediate dates (yet,
    # see commented code in helpers.py:positions_changed()
    secondlast, last = get_last_dates(positions[0])

    log.debug('Loading data for %s' % last)
    json = open(os.path.join(json_path, '%s_%s.json' % (prefix, last)))
    timestamp, nodes, ways, rels, tags = cjson.decode(json.readline())

    make_pickles(prefix, last, nodes, ways, rels, tags, positions)
    log.info("Program ended.")

if __name__ == '__main__':
    from optparse import OptionParser
    import sys

    parser = OptionParser(usage="Usage: %prog [options] dump.osm", version="%prog 0.1")
    parser.add_option("-d", "--date", dest="date", default=None,
        help="set the date, should be in the format YYYYMMDD. If none given, \
it will be inferred from the input filename, which should then be given in the \
form of name.bz2.YYYYMMDD*.")
    parser.add_option("-p", "--prefix", dest="prefix", default="italy",
        help="set the prefix for output files")
    parser.add_option("-q", "--quiet", dest="verbose", action="store_const",
        const=-1, default=0, help="don't output anything to the console.")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_const",
        const=1, help="be verbose on what's being done.")

    options, args = parser.parse_args()

    if not args:
        parser.error('need an OSM dump to work on.')
    else:
        filename = args[0]

    if not options.date:
        # infer the date from the filename
        try:
            options.date = str(int(filename.split('bz2.')[1][:8]))
        except (IndexError, ValueError):
            parser.error('wrong filename, expected name.bz2.YYYYMMDD* to infer date.')

    if options.verbose == -1:
        log.setLevel(logging.NOTSET)
        logh.setLevel(logging.NOTSET)
    elif options.verbose == 1:
        log.setLevel(logging.DEBUG)
        logh.setLevel(logging.DEBUG)

    main(options.prefix, options.date, filename)

