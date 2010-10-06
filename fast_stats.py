#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from genshi.template import MarkupTemplate as template
import xml.etree.cElementTree as etree
from datetime import datetime as dt
import cjson
import os
import logging

from helpers import *

### configuration
html_path = "html/"
jsons_path = "json/"
maxsplit = 100

### logging
log = logging.getLogger('stats')
log.setLevel(logging.INFO)
logh = logging.StreamHandler()
logh.setLevel(logging.INFO)
logfmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logh.setFormatter(logfmt)
log.addHandler(logh)

### data

to_check = {
    "addr:housenumber": [ "*" ],
    "amenity": [
        "bank",
        "bar",
        "bench",
        "clock",
        "college",
        "drinking_water",
        "fast_food",
        "fuel",
        "hospital",
        "parking",
        "pharmacy",
        "place_of_worship",
        "post_box",
        "post_office",
        "pub",
        "restaurant",
        "school",
        "shelter",
        "telephone",
        "university",
        "waste_basket"
    ],
    "barrier" : [ "*" ],
    "bridge" : [ "*" ],
    "building": [
        "*",
        "church",
        "yes",
    ],
    "ele" : [ "*" ],
    "est_width": [ "*" ],
    "height" : [ "*" ],
    "hgv" : [ "*" ],
    "highway": [
        "bus_stop",
        "crossing",
        'cycleway',
        'footway',
        "motorway_junction",
        'path',
        "speed_camera",
        'steps',
        "stop",
        "street_lamp",
        "traffic_lights",
        ('streets', (
            'road',
            'service',
            'pedestrian',
            'living_street',
            'residential',
            'unclassified',
            'tertiary',
            'secondary_link',
            'secondary',
            'primary_link',
            'primary',
            'trunk_link',
            'trunk',
            'motorway_link',
            'motorway',
            'bus_guideway',
        )),
    ],
    "historic" : [ "*" ],
    "leisure": [
        "park",
        "pitch",
        "playground",
    ],
    "lit": [ "*" ],
    "maxspeed": [ "*" ],
    "mtb:scale:*": [ "*" ],
    "natural": [
        "tree",
    ],
    "note": [ "*" ],
    "office": [ "*" ],
    "parking:lane:*": [
        "*",
        "no_parking",
        "no_stopping",
    ],
    "power": [
        "generator",
        "tower"
    ],
    "sac_scale": [ "*" ],
    "shop": [ "*" ],
    "surface" : [ "*" ],
    "tactile_paving": [ "*" ],
    "tracktype" : [ "*" ],
    "traffic_calming" : [ "*" ],
    "tunnel" : [ "*" ],
    "type": [
        "restriction",
        "street",
    ],
    "waterway" : [
        "river",
        "*",
    ],
    "wheelchair": [ "*" ],
    "width" : [ "*" ]
}

### code

def parse(filename):
    log.info("Parsing %s" % filename)
    nodes = defaultdict(int)
    ways = defaultdict(int)
    rels = defaultdict(int)

    tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    source = open(filename)
    context = etree.iterparse(source, events=("start", "end"))
    context = iter(context)

    event, root = context.next()

    for event, elem in context:
        if event == "end":
            root.clear()
            continue

        try:
            if elem.tag == "node":
                nodes[elem.attrib["user"]] += 1
            if elem.tag == "way":
                ways[elem.attrib["user"]] += 1
            if elem.tag == "relation":
                rels[elem.attrib["user"]] += 1
        except KeyError as error:
            if "user" in error.args:
                # This is an object from one of the old "anonymous" users, skip it.
                pass
            else:
                raise error

        for child in elem.getchildren():
            try:
                if child.tag == "tag":
                    key = child.attrib["k"]
                    val = ";".join(sorted(child.attrib["v"].split(";"))) if ";" in child.attrib["v"] else child.attrib["v"]
                    for test in key_wildcard(key):
                        if test in to_check:
                            # first, check for categories-count
                            for v in to_check[test]:
                                if type(v) == tuple:
                                    if val in v[1] or (type(val) == tuple and check_tuple(val, v[1])):
                                        new_v = '%s|%s' % (v[0], ';'.join(v[1]))
                                        tags[test][new_v][elem.attrib['user']] += 1

                            if val in to_check[test] or (type(val) == tuple and check_tuple(val, to_check)):
                                tags[test][val][elem.attrib["user"]] += 1
                            if "*" in to_check[test]:
                                tags[test]["*"][elem.attrib["user"]] += 1
                            break;

            except KeyError as error:
                if "user" in error.args:
                    # This is an object from one of the old "anonymous" users, skip it.
                    pass
                else:
                    raise error

    return [nodes, ways, rels, tags]

def enumerate_tags(tags):
    log.info("Sorting users")
    enum = {}
    enum2 = {}

    for key in tags:
        log.debug("Sorting users for key %s" % key)
        enum[key] = myenum(tags[key])
        enum2[key] = myenum(tags[key], split=maxsplit)

    return [enum, enum2]

def calculate_positions(prefix, date, nodes, ways, rels, tags):
    log.info("Calculating positions")
    try:
        primitives_positions, tags_positions = cjson.decode(open('json/%s_positions.json' % prefix).readline())
    except (IOError, cjson.DecodeError):
        primitives_positions = dict()
        tags_positions = dict()

    primitives_positions[date] = defaultdict(list)
    tags_positions[date] = defaultdict(lambda: defaultdict(list))

    log.debug("Calculating positions for primitives (nodes, ways, relations)")
    for p in [('Nodi', nodes), ('Ways', ways), ('Relazioni', rels)]:
        for user in enumerate(mysort(p[1])):
            primitives_positions[date][p[0]].append(user[1][0])

    for tag in tags:
        log.debug("Calculating positions for key %s" % tag)
        for val in tags[tag]:
            for user in mysort(tags[tag][val]):
                tags_positions[date][tag][val].append(user[0])

    return [primitives_positions, tags_positions]

def save_jsons(prefix, l, pos):
    log.info("Saving to JSON")
    f = open(os.path.join(jsons_path, "%s_%s.json" % (prefix, l[0])), 'w')
    f.write(cjson.encode(l))
    f.close()

    f = open(os.path.join(jsons_path, '%s_positions.json' % prefix), 'w')
    f.write(cjson.encode(pos))
    f.close()

def render_template(prefix, date, nodes, ways, rels, fulltags, splittags, positions):
    log.info("Rendering HTML")

    log.debug('Rendering index page (%s)' % date)
    tmpl = template(open('views/index.tmpl'))
    stream = tmpl.generate(date=date)
    f = open(os.path.join(html_path, 'index.html'), 'w')
    f.write(stream.render('xhtml'))
    f.close()

    log.debug("Rendering primitives pages (%s)" % date)

    for t in [(None, fulltags), (maxsplit, splittags)]:
        tmpl = template(open("views/statistiche.tmpl"))
        stream = tmpl.generate(
                       date=date,
                       nodes=enumerate(mysort(nodes, split=t[0])),
                       ways=enumerate(mysort(ways, split=t[0])),
                       relations=enumerate(mysort(rels, split=t[0])),
                       prefix=prefix,
                       tags=sorted(fulltags.keys()),
                       files=[sanitize(x) for x in sorted(fulltags.keys())],
                       pos=positions_changed(positions[0]),
        )

        if not t[0]:
            # i.e. if t[0] is None, i.e. we're doing the fulltags
            f = open(os.path.join(html_path, '%s_stats_full.html' % prefix), "w")
        else:
            # we're rendering splittags
            f = open(os.path.join(html_path, '%s_stats.html' % prefix), "w")
        f.write(stream.render("xhtml"))
        f.close()

        for key in sorted(t[1].keys()):
            log.debug("Rendering pages for %s=* (%s)" % (key, date))
            stream = template(open('views/key.tmpl')).generate(
                date=date,
                prefix=prefix,
                key=key,
                vals=t[1][key],
                pos=positions_changed(positions[1])[key],
                split=t[0],
            )
            if not t[0]:
                # i.e. if t[0] is None, i.e. we're doing the fulltags
                f = open(os.path.join(html_path, '%s_%s_full.html' % (prefix, sanitize(key))), 'w')
            else:
                # we're rendering splittags
                f = open(os.path.join(html_path, '%s_%s.html' % (prefix, sanitize(key))), 'w')
            f.write(stream.render('xhtml'))
            f.close()

def main(prefix, date, filename):
    nodes, ways, rels, tags = parse(filename)
    positions = calculate_positions(prefix, date, nodes, ways, rels, tags)
    save_jsons(prefix, [date, nodes, ways, rels, tags], positions)

    # render the last date, we don't support rendering intermediate dates (yet,
    # see commented code in helpers.py:positions_changed()
    secondlast, last = get_last_dates(positions[0])

    log.debug('Loading data for %s' % last)
    json = open(os.path.join(jsons_path, '%s_%s.json' % (prefix, last)))
    timestamp, nodes, ways, rels, tags = cjson.decode(json.readline())

    enum, enum2 = enumerate_tags(tags)
    render_template(prefix, last, nodes, ways, rels, enum, enum2, positions)
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

