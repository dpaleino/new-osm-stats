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
import os

from config import *
from osmstats.output.pickle import make_pickles


def main(prefix, date):
    json = open(os.path.join(json_path, '%s_%s.json' % (prefix, date)))
    pos = open(os.path.join(json_path, '%s_positions.json' % prefix))

    timestamp, nodes, ways, rels, tags = cjson.decode(json.readline())
    positions = cjson.decode(pos.readline())

    make_pickles(prefix, date, nodes, ways, rels, tags, positions)

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage="Usage: %prog [options]", version="%prog 0.1")
    parser.add_option("-d", "--date", dest="date", default=None,
        help="set the date, should be in the format YYYYMMDD")
    parser.add_option("-p", "--prefix", dest="prefix", default="italy",
        help="set the prefix for input files")

    options, args = parser.parse_args()

    if not options.date:
        parser.error('a date is needed.')

    main(options.prefix, options.date)

