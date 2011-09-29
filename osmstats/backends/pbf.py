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
# PBF Input Backend
###############################################################################

from collections import defaultdict
from google.protobuf import message
import fileformat_pb2 as filepbf
import logging
import osmformat_pb2 as osmpbf
import struct
import sys
import zlib
import time
from itertools import izip_longest

from helpers import *
from config import *
from tags import to_check

stringtable = None
nodes = defaultdict(int)
ways = defaultdict(int)
rels = defaultdict(int)
tags = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def list_split(l):
    """
    Splits the keys_vals list for each node
    """
    tmp = []
    ret = []
    for i in l:
        if i == 0:
            ret.append(tmp)
            tmp = []
        else:
            tmp.append(i)
    return ret


def parse_primitive_group(group):
    global nodes, ways, rels

    # Check if there is a DenseNodes block
    if group.dense.id:
        last_user = 0
        i = 0

        nodelist = filter(None, list_split(group.dense.keys_vals))
        for node in nodelist:
            # Delta coded!
            # TODO: handle anonymous users
            last_user += group.dense.denseinfo.user_sid[i]
            i += 1
            nodes[stringtable[last_user]] += 1
            for tag in izip_longest(*[iter(node)] * 2):
                key_val = map(stringtable.__getitem__, tag)
                handle_tags(stringtable[last_user], key_val)
#                print stringtable[last_user],
#                print 'node', '='.join(map(stringtable.__getitem__, tag))

    # Uncompressed primitives
    for node in group.nodes:
        nodes[stringtable[node.info.user_sid]] += 1
        for tag in zip(node.keys, node.vals):
            key_val = map(stringtable.__getitem__, tag)
            handle_tags(stringtable[node.info.user_sid], key_val)
#            print stringtable[node.info.user_sid],
#            print 'node', '='.join(map(stringtable.__getitem__, tag))
    for way in group.ways:
        ways[stringtable[way.info.user_sid]] += 1
        for tag in zip(way.keys, way.vals):
            key_val = map(stringtable.__getitem__, tag)
            handle_tags(stringtable[way.info.user_sid], key_val)
#            print stringtable[way.info.user_sid],
#            print 'way', '='.join(map(stringtable.__getitem__, tag))
#        sys.exit(1)
    for relation in group.relations:
        rels[stringtable[relation.info.user_sid]] += 1
        for tag in zip(relation.keys, relation.vals):
            key_val = map(stringtable.__getitem__, tag)
            handle_tags(stringtable[relation.info.user_sid], key_val)
#            print stringtable[relation.info.user_sid],
#            print 'relation', '='.join(map(stringtable.__getitem__, tag))


def handle_tags(user, key_val):
    global tags
    key, value = key_val

    value = ";".join(sorted(value.split(";"))) if ";" in value else value
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


def parse_pbf(file):
    global stringtable
    block_count = 0

    header = filepbf.BlobHeader()
    blob = filepbf.Blob()
    header_block = osmpbf.HeaderBlock()
    primitive_block = osmpbf.PrimitiveBlock()

    input_stream = open(file, 'rb')

    eof = False
    while not eof:
        data = input_stream.read(4)
        eof = not data
        if not eof:
            header_size = struct.unpack(">i", data)[0]
            data = input_stream.read(header_size)
            block_count += 1
            header.ParseFromString(data)
            blob_size = header.datasize
            blob_stream = input_stream.read(blob_size)
            blob.ParseFromString(blob_stream)
            if header.type == 'OSMHeader':
                try:
                    header_data = zlib.decompress(blob.zlib_data)
                except zlib.error:
                    header_data = blob.raw
                header_block.ParseFromString(header_data)
                bbox = header_block.bbox
#                print 'BBOX: %s,%s,%s,%s' % (bbox.top, bbox.right, bbox.bottom, bbox.left)
            elif header.type == 'OSMData':
                try:
                    primitive_data = zlib.decompress(blob.zlib_data)
                except zlib.error:
                    primitive_data = blob.raw
                primitive_block.ParseFromString(primitive_data)
                stringtable = primitive_block.stringtable.s
                for primitive_group in primitive_block.primitivegroup:
                    parse_primitive_group(primitive_group)

    input_stream.close()


def parse(file):
    parse_pbf(file)
    return [nodes, ways, rels, tags]
