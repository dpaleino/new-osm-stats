#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from operator import itemgetter
import Gnuplot
from genshi.template import MarkupTemplate as template
import xml.etree.cElementTree as etree
from datetime import datetime as dt
import cjson

from helpers import mysort, myenum, key_wildcard

### configuration
html_path = "statistiche.html"
timestamp = dt.strftime(dt.today(), "%Y%m%dT%H:%S%Z")

### data

sheer_nodes = defaultdict(int)
sheer_ways = defaultdict(int)
sheer_rels = defaultdict(int)

tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
to_check = {
    "addr:housenumber": [ "*" ],
    "amenity": [
        "drinking_water",
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

source = open(sys.argv[1])
context = etree.iterparse(source, events=("start", "end"))
context = iter(context)

event, root = context.next()

for event, elem in context:
    try:
        if elem.tag == "node":
            sheer_nodes[elem.attrib["user"]] += 1
        if elem.tag == "way":
            sheer_ways[elem.attrib["user"]] += 1
        if elem.tag == "relation":
            sheer_rels[elem.attrib["user"]] += 1
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
                val = tuple(sorted(child.attrib["v"].split(";"))) if ";" in child.attrib["v"] else child.attrib["v"]
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

    if event == "end":
        root.clear()

#g = Gnuplot.Gnuplot(debug=1)
#g.title("A simple example")
#g("set style data linespoints")
#g("set output 'foo.png'")
#g("set terminal png")
#g.plot([[0,1.1], [1,5.8], [2,3.3], [3,4.2]])

enum = {}
for key in tags:
    enum[key] = myenum(tags[key])

save = [timestamp, sheer_nodes, sheer_ways, sheer_rels, tags]
f = open("json/%s.json" % timestamp.split('T')[0], 'w')
f.write(cjson.encode(save))
f.close()

tmpl = template(open("views/statistiche.tmpl"))
stream = tmpl.generate(
                       date=timestamp,
                       nodes=enumerate(mysort(sheer_nodes)),
                       ways=enumerate(mysort(sheer_ways)),
                       relations=enumerate(mysort(sheer_rels)),
                       tags=enum,
         )

f = open(html_path, "w")
f.write(stream.render("xhtml"))
f.close()
