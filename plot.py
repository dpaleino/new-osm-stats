#!/usr/bin/env python
# -*- coding: utf-8 -*-

from glob import iglob
import cjson
import Gnuplot
from collections import defaultdict

graphs_path = 'graphs/'

def plot(xcoords, ycoords, file):
    print xcoords, ycoords
    print zip(*ycoords)
    import matplotlib.pyplot as plt
    import matplotlib.dates as dts
    from datetime import datetime
    
    years = dts.YearLocator()
    months = dts.MonthLocator()
    yearsFmt = dts.DateFormatter('%Y')
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    styles = ['bo-', 'kx-', 'y+-', 'go-', 'rx-']
    i = 0
    while i < len(zip(*ycoords)):
        l = zip(*ycoords)[i]
        ax.plot_date(map(lambda x: dts.date2num(datetime.strptime(x, '%Y%m%d')), xcoords), zip(*l)[1], styles[i], label=zip(*l)[0])
        i += 1
#    ax.xaxis.set_major_locator(years)
#    ax.xaxis.set_major_formatter(yearsFmt)
#    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_major_locator(months)
    
    fig.autofmt_xdate()
    fig.suptitle(file)
    plt.savefig('%s/%s.png' % (graphs_path, file))
    plt.close()

search_tags = ["highway=bus_stop", "addr:housenumber=*"]
search_users = ["David Paleino", "trimoto", "Gianfra"] #, "tosky"]

xcoords = []
counts = defaultdict(dict)
ycoords = defaultdict(list)

for i in iglob('json/sicilia_*.json'):
    load = cjson.decode(open(i).readline())
    timestamp = load[0]
    nodes = load[1]
    ways = load[2]
    rels = load[3]
    tags = load[4]

    xcoords.append(timestamp.split('T')[0])

    l = [nodes, ways, rels]
    for d in l:
        tmpcount = 0
        for c in d:
            tmpcount += d[c]

        if l.index(d) == 0:
            counts[timestamp]["nodes"] = tmpcount
        elif l.index(d) == 1:
            counts[timestamp]["ways"] = tmpcount
        elif l.index(d) == 2:
            counts[timestamp]["rels"] = tmpcount

    for tag in search_tags:
        key, val = tag.split('=', 1)
        ydate = []
        for user in search_users:
            try:
                ydate.append((user, tags[key][val][user]))
                print "%s: %s" % (user, tags[key][val][user])
            except KeyError:
                print "%s: %s" % (user, "0")
        ycoords[tag].append(ydate)

print counts
for tag in search_tags:
    plot(xcoords, ycoords[tag], tag)

#g = Gnuplot.Gnuplot(debug=1)
#g.title("A simple example")
#g("set style data linespoints")
#g("set output 'foo.png'")
#g("set terminal png")
#g.plot([[0,1.1], [1,5.8], [2,3.3], [3,4.2]])
