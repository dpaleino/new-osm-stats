#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from genshi.template import MarkupTemplate as template
import xml.etree.cElementTree as etree
from datetime import datetime as dt
import cjson

from helpers import *

### configuration
html_path = "statistiche.html"
timestamp = dt.strftime(dt.today(), "%Y%m%d")

### data

to_check = {
    "addr:housenumber": [ "*" ],
    "amenity": [
        "drinking_water",
        "post_box",
        "telephone",
    ],
    "highway": [
        "bus_stop",
    ],
    "building": [
        "*",
        "yes",
        "church",
    ],
    "parking:lane:*": [
        "*",
        "no_parking",
        "no_stopping",
    ],
}

### code

def parse(filename):
    nodes = defaultdict(int)
    ways = defaultdict(int)
    rels = defaultdict(int)

    tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    source = open(sys.argv[1])
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

def calculate_positions(nodes, ways, rels, enum):
    try:
        primitives_positions, tags_positions = cjson.decode(open('json/positions.json').readline())
    except (IOError, cjson.DecodeError):
        primitives_positions = dict()
        tags_positions = dict()

    primitives_positions[timestamp] = defaultdict(list)
    tags_positions[timestamp] = defaultdict(lambda: defaultdict(list))

    for p in [('Nodi', nodes), ('Ways', ways), ('Relazioni', rels)]:
        for user in enumerate(mysort(p[1])):
            primitives_positions[timestamp][p[0]].append(user[1][0])

    for tag in enum:
        for val in enum[tag]:
            for user in enum[tag][val]:
                tags_positions[timestamp][tag][val].append(user[1][0])

    return [primitives_positions, tags_positions]

def save_jsons(l, pos):
#    save = [timestamp, sheer_nodes, sheer_ways, sheer_rels, tags]
    f = open("json/%s.json" % timestamp, 'w')
    f.write(cjson.encode(l))
    f.close()

    f = open('json/positions.json', 'w')
    f.write(cjson.encode(pos))
    f.close()

def render_template(nodes, ways, rels, tags, positions):
    tmpl = template(open("views/statistiche.tmpl"))
    stream = tmpl.generate(
                       date=timestamp,
                       nodes=enumerate(mysort(nodes)),
                       ways=enumerate(mysort(ways)),
                       relations=enumerate(mysort(rels)),
                       tags=tags,
                       pos_primitives=positions_changed(positions[0]),
                       pos_tags=positions_changed(positions[1]),
    )

    f = open(html_path, "w")
    f.write(stream.render("xhtml"))
    f.close()

def main():
    nodes, ways, rels, tags = parse(sys.argv[1])
    enum, enum2 = enumerate_tags(tags)
    positions = calculate_positions(nodes, ways, rels, enum)
    save_jsons([timestamp, nodes, ways, rels, tags], positions)
    render_template(nodes, ways, rels, enum2, positions)

if __name__ == '__main__':
    main()

