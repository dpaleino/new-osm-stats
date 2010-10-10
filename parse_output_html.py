#!/usr/bin/env python

# Copyright © 2010, David Paleino <d.paleino@gmail.com>
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

save = [timestamp, nodes, ways, rels, tags]

print cjson.encode(save)
