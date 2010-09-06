#!/usr/bin/env python
# -*- coding: utf-8 -*-

from glob import glob
import cjson
import Gnuplot
import tempfile
import os
from collections import defaultdict

graphs_path = 'graphs/'

class Graph():
    def __init__(self, filename, title=None):
        self.file = filename
        self.title = title if title else self.file
        self.user = False
        self.tmp = []

        self.g = Gnuplot.Gnuplot(debug=1)
        self.g.title(self.title)
        self.g("set style data linespoints")
        self.g("set output '%s.svg'" % os.path.join(graphs_path, self.file))
        self.g("set terminal svg")
        self.g("set xdata time")
        self.g("set timefmt '%Y%m%d'")
        self.g("set format x '%m/%y'")

    def add_line(self, user, xcoords, ycoords):
        tmpfile = tempfile.mkstemp()[1]
        self.tmp.append((user, tmpfile))

        xcoords = map(lambda x: x.split('T')[0], xcoords)
        print xcoords, ycoords

        f = open(tmpfile, 'w')
        for x, y in zip(xcoords, ycoords):
            f.write('%(x)s %(y)s\n' % locals())
            self.g("set label '%(y)s' at '%(x)s',%(y)s" % locals())
        f.close()

    def plot(self):
        l = []
        for user, tmpfile in self.tmp:
            l.append("'%s' using 1:2 title '%s'" % (tmpfile, user))
        self.g("plot " + ', '.join(l))
        self.g.close()
        for user, tmpfile in self.tmp:
            os.unlink(tmpfile)


search_tags = ["highway=bus_stop", "addr:housenumber=*"]
search_users = ["David Paleino", "trimoto", "Gianfra"] #, "tosky"]

xcoords = []
counts = []
ycoords = defaultdict(list)

for i in sorted(glob('json/italy_*.json')):
    load = cjson.decode(open(i).readline())
    timestamp = load[0]
    nodes = load[1]
    ways = load[2]
    rels = load[3]
    tags = load[4]

    xcoords.append(timestamp.split('T')[0])

    l = [nodes, ways, rels]
    counts.append([])
    for d in l:
        tmpcount = 0
        for c in d:
            tmpcount += int(d[c])

        counts[-1].append(tmpcount)
#        if l.index(d) == 0:
#            counts[timestamp]["nodes"] = tmpcount
#        elif l.index(d) == 1:
#            counts[timestamp]["ways"] = tmpcount
#        elif l.index(d) == 2:
#            counts[timestamp]["rels"] = tmpcount

    for tag in search_tags:
        key, val = tag.split('=', 1)
        ydate = []
        for user in search_users:
            try:
                count = tags[key][val][user]
            except KeyError:
                count = 0
            ydate.append((user, count))
        ycoords[tag].append(ydate)
    del l

titles = ['Nodes', 'Ways', 'Relations']
for t in titles:
    graph = Graph(t)
    graph.add_line(t, xcoords, zip(*counts)[titles.index(t)])
    graph.plot()

for tag in search_tags:
    graph = Graph(tag)
    for user in zip(*ycoords[tag]):
        graph.add_line(zip(*user)[0][0], xcoords, zip(*user)[1])
    graph.plot()
