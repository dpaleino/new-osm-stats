#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        self.g("set style data lines")
        self.g("set output '%s'" % self.file)
        self.g("set terminal svg font 'sans-serif'")
        self.g("set xdata time")
        self.g("set timefmt '%Y%m%d'")
        self.g("set format x '%m/%y'")
        self.g("set key left top")

    def add_line(self, user, xcoords, ycoords):
        tmpfile = tempfile.mkstemp()[1]
        self.tmp.append((user, tmpfile))

        f = open(tmpfile, 'w')
        couples = zip(xcoords, ycoords)
#        i = 0 # number of parsings
#        every = len(couples) / 5 # (we only want 5 labels)
        for x, y in sorted(zip(xcoords, ycoords), key=itemgetter(0)):
            f.write('%(x)s %(y)s\n' % locals())
#            i += 1
#            if int(every) == 0 or (i % every) == 0:
#                self.g("set label '%(y)s' at '%(x)s',%(y)s" % locals())
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

if __name__ == "__main__":
    counts, xcoords, ycoords = parse_json()
    titles = ['Nodes', 'Ways', 'Relations']
    for t in titles:
        graph = Graph(os.path.join(graphs_path, "%s.svg" % t), t)
        graph.add_line(t, xcoords, zip(*counts)[titles.index(t)])
        graph.plot()
