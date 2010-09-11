#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from genshi.template import MarkupTemplate as template
import xml.etree.cElementTree as etree
from datetime import datetime as dt
import cjson
import os

from helpers import *

### configuration
html_path = "html/"
jsons_path = "json/"

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
        "motorway_junction",
        "speed_camera",
        "stop",
        "street_lamp",
        "traffic_lights",
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
                            if val in to_check[test] or (type(val) == tuple and (val[0] in to_check or val[1] in to_check)):
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
    enum = {}
    enum2 = {}

    for key in tags:
        enum[key] = myenum(tags[key])
        enum2[key] = myenum(tags[key])

    return [enum, enum2]

def calculate_positions(prefix, date, nodes, ways, rels, enum):
    try:
        primitives_positions, tags_positions = cjson.decode(open('json/%s_positions.json' % prefix).readline())
    except (IOError, cjson.DecodeError):
        primitives_positions = dict()
        tags_positions = dict()

    primitives_positions[date] = defaultdict(list)
    tags_positions[date] = defaultdict(lambda: defaultdict(list))

    for p in [('Nodi', nodes), ('Ways', ways), ('Relazioni', rels)]:
        for user in enumerate(mysort(p[1])):
            primitives_positions[date][p[0]].append(user[1][0])

    for tag in enum:
        for val in enum[tag]:
            for user in enum[tag][val]:
                tags_positions[date][tag][val].append(user[1][0])

    return [primitives_positions, tags_positions]

def save_jsons(prefix, l, pos):
    f = open(os.path.join(jsons_path, "%s_%s.json" % (prefix, l[0])), 'w')
    f.write(cjson.encode(l))
    f.close()

    f = open(os.path.join(jsons_path, '%s_positions.json' % prefix), 'w')
    f.write(cjson.encode(pos))
    f.close()

def render_template(prefix, date, nodes, ways, rels, tags, positions):
    tmpl = template(open("views/statistiche.tmpl"))
    stream = tmpl.generate(
                       date=date,
                       nodes=enumerate(mysort(nodes)),
                       ways=enumerate(mysort(ways)),
                       relations=enumerate(mysort(rels)),
                       tags=tags,
                       pos_primitives=positions_changed(positions[0]),
                       pos_tags=positions_changed(positions[1]),
    )

    f = open(os.path.join(html_path, '%s_stats.html' % prefix), "w")
    f.write(stream.render("xhtml"))
    f.close()

def main(prefix, date, filename):
    nodes, ways, rels, tags = parse(filename)
    enum, enum2 = enumerate_tags(tags)
    positions = calculate_positions(prefix, date, nodes, ways, rels, enum)
    save_jsons(prefix, [date, nodes, ways, rels, tags], positions)
    render_template(prefix, date, nodes, ways, rels, enum2, positions)

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

    options, args = parser.parse_args()

    if not args:
        parser.error('need an OSM dump to work on.')
    else:
        filename = args[0]

    if not options.date:
        # infer the date from the filename
        try:
            options.date = int(filename.split('bz2.')[1][:8])
        except (IndexError, ValueError):
            parser.error('wrong filename, expected name.bz2.YYYYMMDD* to infer date.')

    main(options.prefix, options.date, filename)

