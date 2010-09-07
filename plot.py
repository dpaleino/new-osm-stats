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
        self.g("set output '%s'" % self.file)
        self.g("set terminal svg font 'sans-serif'")
        self.g("set xdata time")
        self.g("set timefmt '%Y%m%d'")
        self.g("set format x '%m/%y'")

    def add_line(self, user, xcoords, ycoords):
        tmpfile = tempfile.mkstemp()[1]
        self.tmp.append((user, tmpfile))

        xcoords = map(lambda x: x.split('T')[0], xcoords)

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

def graph_tag_users(tags, users):
    counts, xcoords, ycoords = parse_json()
    files = []

    if type(tags) != list:
        tags = [tags]
    if type(users) != list:
        users = [users]

    for tag in tags:
        filename = tempfile.mkstemp()[1]
        files.append(filename)
        graph = Graph(filename, tag)

        for user in users:
            user_y = [ ycoords[tag][x][user] for x in sorted(ycoords[tag].keys()) ]
            graph.add_line(user, xcoords, user_y)

        graph.plot()
    return files

def parse_json(full=False):
    xcoords = []
    counts = []
    ycoords = defaultdict(dict)

    if full:
        d_nodes = {}
        d_ways = {}
        d_rels = {}

    for i in sorted(glob('json/italy_*.json')):
        load = cjson.decode(open(i).readline())
        timestamp = load[0]
        timestamp = timestamp.split('T')[0]
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
