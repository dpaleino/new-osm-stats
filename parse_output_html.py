#!/usr/bin/env python

from lxml import etree
import sys
from collections import defaultdict
import cjson
from datetime import datetime as dt

nodes={}
ways={}
rels={}
tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
timestamp = dt.strftime(dt.today(), "%Y%m%dT%H:%S%Z")

doc = etree.parse(sys.argv[1])
for node in doc.xpath('/body/div/div[@name="Nodi"]/table/tbody/tr'):
    nodes[node[1].text] = node[2].text

for node in doc.xpath('/body/div/div[@name="Ways"]/table/tbody/tr'):
    ways[node[1].text] = node[2].text

for node in doc.xpath('/body/div/div[@name="Relazioni"]/table/tbody/tr'):
    rels[node[1].text] = node[2].text

for node in doc.xpath('/body/div/div/div[@class="feature"]'):
    key, val = node[0].attrib["name"].split('=')
    for row in node[2].xpath('tbody/tr'):
        tags[key][val][row[1].text] = int(row[2].text)

s  = cjson.encode(timestamp)
s += cjson.encode(nodes)
s += cjson.encode(ways)
s += cjson.encode(rels)
s += cjson.encode(tags)

print s
