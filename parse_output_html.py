#!/usr/bin/env python

from lxml import etree
import sys
from collections import defaultdict
from simplejson import JSONEncoder
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

json = JSONEncoder()
s  = json.encode(timestamp)
s += json.encode(nodes)
s += json.encode(ways)
s += json.encode(rels)
s += json.encode(tags)

print s
