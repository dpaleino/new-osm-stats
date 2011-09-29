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

from collections import defaultdict
import cjson
import os

from config import *
from osmstats.backends.osmxml import parse
from osmstats.helpers import *
from osmstats.output.json import save_jsons
from osmstats.output.pickle import make_pickles
from osmstats.output.html import make_footer
from osmstats.positions import *

### code

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

    parser = OptionParser(usage="Usage: %prog [options] dump.osm", version="OSMStats "+version)
    parser.add_option("-d", "--date", dest="date", default=None,
        help="set the date, should be in the format YYYYMMDD")
    parser.add_option("-p", "--prefix", dest="prefix", default=None,
        help="set the prefix for output files")
    parser.add_option("-q", "--quiet", dest="verbose", action="store_const",
        const=-1, default=0, help="don't output anything to the console.")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_const",
        const=1, help="be verbose on what's being done.")

    options, args = parser.parse_args()

    if not args:
        parser.error('need an OSM dump to work on.')

    if not options.date:
        parser.error('need a date in the format YYYYMMDD.')

    if not options.prefix:
        parser.error('need a prefix.')

    if options.verbose == -1:
        log.setLevel(logging.NOTSET)
        logh.setLevel(logging.NOTSET)
    elif options.verbose == 1:
        log.setLevel(logging.DEBUG)
        logh.setLevel(logging.DEBUG)

    main(options.prefix, options.date, args[0])

