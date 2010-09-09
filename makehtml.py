#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fast_stats as stats
import cjson
import os

def main(prefix, date):
    json = open(os.path.join(stats.jsons_path, '%s_%s.json' % (prefix, date)))
    pos = open(os.path.join(stats.jsons_path, '%s_positions.json' % prefix))

    timestamp, nodes, ways, rels, tags = cjson.decode(json.readline())
    positions = cjson.decode(pos.readline())

    stats.render_template(prefix, date, nodes, ways, rels, stats.enumerate_tags(tags)[0], positions)


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

