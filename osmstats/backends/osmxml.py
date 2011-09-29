#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2011, David Paleino <d.paleino@gmail.com>
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

###############################################################################
# XML Input Backend
###############################################################################

from collections import defaultdict
import xml.etree.cElementTree as etree

from osmstats.helpers import *
from config import *
from tags import to_check

nodes = defaultdict(int)
ways = defaultdict(int)
rels = defaultdict(int)
tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def parse_xml(file):
    log.info("Parsing %s" % file)

    source = open(file)
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
                    handle_tags(elem.attrib['user'], (key, val))
            except KeyError as error:
                if "user" in error.args:
                    # This is an object from one of the old "anonymous" users, skip it.
                    pass
                else:
                    raise error


def handle_tags(user, key_val):
    global tags
    key, value = key_val

    for test in key_wildcard(key):
        if test in to_check:
            # first, check for categories-count
            for v in to_check[test]:
                if type(v) == tuple:
                    if value in v[1] or (type(value) == tuple and check_tuple(value, v[1])):
                        new_v = '%s|%s' % (v[0], ';'.join(v[1]))
                        tags[test][new_v][user] += 1

            if value in to_check[test] or (type(value) == tuple and check_tuple(value, to_check)):
                tags[test][value][user] += 1
            if "*" in to_check[test]:
                tags[test]["*"][user] += 1
            break


def parse(file):
    parse_xml(file)
    return [nodes, ways, rels, tags]
