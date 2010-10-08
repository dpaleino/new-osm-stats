#!/usr/bin/env python
# -*- coding: utf-8 -*-

from glob import glob
import cjson
import Gnuplot
import tempfile
import os
from collections import defaultdict
import hashlib
from operator import itemgetter

from config import *

class Graph():
    def __init__(self, filename, title=None):
        self.file = filename
        self.title = title if title else self.file
        self.user = False
        self.tmp = []

        self.g = Gnuplot.Gnuplot(debug=1)
        self.g.title(self.title)
        self.g("set style data linespoints")
        self.g("set output '%s'" % self.file)
        self.g("set terminal svg font 'sans-serif'")
        self.g("set xdata time")
        self.g("set timefmt '%Y%m%d'")
        self.g("set format x '%m/%y'")
        self.g("set key left top")

    def add_line(self, user, xcoords, ycoords):
        tmpfile = tempfile.mkstemp()[1]
        self.tmp.append((user, tmpfile))

        xcoords = map(lambda x: x.split('T')[0], xcoords)

        f = open(tmpfile, 'w')
        couples = zip(xcoords, ycoords)
        i = 0 # number of parsings
        every = len(couples) / 5 # (we only want 5 labels)
        for x, y in sorted(zip(xcoords, ycoords), key=itemgetter(0)):
            f.write('%(x)s %(y)s\n' % locals())
            i += 1
            if (i % every) == 0:
                self.g("set label '%(y)s' at '%(x)s',%(y)s" % locals())
        f.close()

    def plot(self):
        l = []
        for user, tmpfile in self.tmp:
            # support "categories"
            if '|' in user and ';' in user.split('|')[1]:
                label = user.split('|')[0]
            else:
                label = user
            l.append("'%s' using 1:2 title '%s'" % (tmpfile, label))
        self.g("plot " + ', '.join(l))
        self.g.close()
        for user, tmpfile in self.tmp:
            os.unlink(tmpfile)

def graph_tag_users(prefix, tags, users):
    counts, xcoords, ycoords = parse_json(prefix)
    files = []

    if type(tags) != list:
        tags = [tags]
    if type(users) != list:
        users = [users]

    tags = sorted(filter(None, tags))
    users = sorted(filter(None, users))

    for tag in tags:
        filename = hashlib.md5(repr([tag, users, ycoords[tag].keys()])).hexdigest()
        filename = os.path.join(graphs_cache, filename)
        files.append(filename)

        if filename in glob(os.path.join(graphs_cache, '*')):
            # we'll return the cached one
            continue

        graph = Graph(filename, tag)

        for user in users:
            user_y = [ ycoords[tag][x][user] for x in sorted(ycoords[tag].keys()) ]
            graph.add_line(user, xcoords, user_y)

        graph.plot()
    return files

def graph_totals(prefix, tags):
    counts, xcoords, ycoords = parse_json(prefix)

    if type(tags) != list:
        tags = [tags]
    tags = sorted(filter(None, tags))

    filename = hashlib.md5(repr([tags, ycoords[tags[0]].keys()])).hexdigest()
    filename = os.path.join(graphs_cache, filename)

    if filename in glob(os.path.join(graphs_cache, '*')):
       # we'll return the cached one
       return filename

    graph = Graph(filename, 'Tag comparison')
    for tag in tags:
        yvalues = []
        for key in ycoords[tag]:
            val = 0
            for user in ycoords[tag][key]:
                val += ycoords[tag][key][user]
            yvalues.append(val)
        graph.add_line(tag, ycoords[tag].keys(), yvalues)
    graph.plot()

    return filename

def parse_json(prefix, full=False):
    xcoords = []
    counts = []
    ycoords = defaultdict(dict)

    if full:
        d_nodes = {}
        d_ways = {}
        d_rels = {}

    for i in sorted(glob(os.path.join(json_path, prefix) + '_*.json')):
        if 'positions' in i or 'tags_users' in i:
            continue

        load = cjson.decode(open(i).readline())
        timestamp = load[0]
        nodes = load[1]
        ways = load[2]
        rels = load[3]
        tags = load[4]

        if full:
            d_nodes[timestamp] = nodes
            d_ways[timestamp] = ways
            d_rels[timestamp] = rels

        xcoords.append(timestamp)

        l = [nodes, ways, rels]
        counts.append([])
        for d in l:
            tmpcount = 0
            for c in d:
                tmpcount += int(d[c])

            counts[-1].append(tmpcount)

        for key in tags:
            for val in tags[key]:
                date = defaultdict(int)
                for user in tags[key][val]:
                    date[user] = tags[key][val][user]
                ycoords["%s=%s" % (key,val)][timestamp] = date

        del l

    if full:
        return (d_nodes, d_ways, d_rels, xcoords, ycoords)
    else:
        return (counts, xcoords, ycoords)

if __name__ == "__main__":
    counts, xcoords, ycoords = parse_json()
    titles = ['Nodes', 'Ways', 'Relations']
    for t in titles:
        graph = Graph(os.path.join(graphs_path, "%s.svg" % t), t)
        graph.add_line(t, xcoords, zip(*counts)[titles.index(t)])
        graph.plot()
