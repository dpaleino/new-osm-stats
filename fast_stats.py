#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as etree
#from lxml import etree

import sys
from collections import defaultdict
from operator import itemgetter
import Gnuplot
from genshi.template import MarkupTemplate as template


### configuration
html_path = "statistiche.html"


### data

sheer_nodes = defaultdict(int)
sheer_ways = defaultdict(int)
sheer_rels = defaultdict(int)

tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
to_check = {
    "amenity": [
        "drinking_water",
    ],
    "highway": [
        "bus_stop",
    ],
    "building": [
        "yes",
        "church",
    ],
}

amenities = defaultdict(lambda: defaultdict(int))
highways = defaultdict(lambda: defaultdict(int))
buildings = defaultdict(lambda: defaultdict(int))

### helpers

def mysort(d):
    return sorted(d.items(), key=itemgetter(1), reverse=True)

def tagsort(d):
    tmp = defaultdict(list)
    for k in d:
        tmp[k] = mysort(d[k])
    return tmp

def myenum(d):
    enum = {}
    for key in d:
        enum[key] = enumerate(mysort(d[key]))
    return enum

### code

source = open(sys.argv[1])
context = etree.iterparse(source, events=("start", "end"))
context = iter(context)

event, root = context.next()

try:
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
#                    print ";" in child.attrib["v"]
#                    print repr(val)
#                    print repr(sorted(tuple(child.attrib["v"].split(";"))))
#                    print repr(child.attrib["v"])
                    if key in to_check:
                        if val in to_check[key] or (type(val) == tuple and (val[0] in to_check or val[1] in to_check)):
                            tags[key][val][elem.attrib["user"]] += 1
            except KeyError as error:
                if "user" in error.args:
                    # This is an object from one of the old "anonymous" users, skip it.
                    pass
                else:
                    raise error

except:
    print repr(elem.tag), repr(elem.attrib)
    sys.exit(1)

    if event == "end":
        root.clear()

#print mysort(sheer_nodes)
#print mysort(sheer_ways)
#print mysort(sheer_rels)
#print "highways:", tagsort(highways)
#print "amenities:", tagsort(amenities)

#g = Gnuplot.Gnuplot(debug=1)
#g.title("A simple example")
#g("set style data linespoints")
#g("set output 'foo.png'")
#g("set terminal png")
#g.plot([[0,1.1], [1,5.8], [2,3.3], [3,4.2]])

enum = {}
for key in tags:
    enum[key] = myenum(tags[key])

tmpl = template(open("views/statistiche.tmpl"))
stream = tmpl.generate(
                       date="#DATE#",
                       nodes=enumerate(mysort(sheer_nodes)),
                       ways=enumerate(mysort(sheer_ways)),
                       relations=enumerate(mysort(sheer_rels)),
                       tags=enum,
         )

f = open(html_path, "w")
f.write(stream.render("xhtml"))
f.close()

#g.hardcopy(filename="foo.png", terminal="png")
