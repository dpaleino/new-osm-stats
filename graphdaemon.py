#!/usr/bin/python
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

import os
import sys

import threading
from fcntl import lockf, LOCK_EX, LOCK_NB
from signal import pause
from time import sleep

from Queue import Queue, Empty
import logging
import pyinotify
import cPickle as pickle
from glob import glob
from collections import defaultdict

from plot import *
from config import *

running = True
log = None

class PE(pyinotify.ProcessEvent):
    def __init__(self, main):
        pyinotify.ProcessEvent.__init__(self)
        self.main = main

    def process_IN_CLOSE_WRITE(self, event):
        if event.name == 'RELOAD':
            self.main.load_data()
            return
        self.main.add_to_queue(event)

class GraphDaemon(object):
    def __init__(self):
        #self.daemonize()
        self.queue = Queue()
        self.notifier = None
        self.data = None
        self.load_data()

        # lock
        fd = os.open('/tmp/graph.lock', os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        try:
            lockf(fd, LOCK_EX | LOCK_NB)
        except IOError:
            log.error('Another instance running, aborting.')
            sys.exit(-1)

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            log.error('Cannot enter daemon mode')
            sys.exit(-1)
        os.setsid()
        os.chdir('/')
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            log.error('Cannot enter daemon mode')
            sys.exit(-1)
        fin = open('/dev/null', 'r')
        fout = open('/dev/stdout', 'a+')
        ferr = open('/dev/stderr', 'a+', 0)
        os.dup2(fin.fileno(), sys.stdin.fileno())
        os.dup2(fout.fileno(), sys.stdout.fileno())
        os.dup2(ferr.fileno(), sys.stderr.fileno())

    def start(self):
        threading.Thread(None, self.loop).start()

        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(wm, PE(self))
        wm.add_watch(graphs_cmddir, pyinotify.IN_CLOSE_WRITE, rec=True)
        self.notifier.start()

        try:
            pause()
        except KeyboardInterrupt:
            log.info('Waiting for threads to finish, it could take a while...')
            self.notifier.stop()
            exit_routine(exiting=True)

    def loop(self):
        global running
        while True:
            item = self.queue.get()
            running = True
            log.info(item)
            self.make_graph(pickle.load(open(item.pathname)))
            try:
                os.unlink(item.pathname)
            except IOError:
                pass
            self.queue.task_done()
#            running = False
            exit_routine()

    def make_graph(self, data):
        """
        data is a dict containing the data to graph, structured as follows:
        
        {
         'filename': '',
         'type': 'graph-tag-users' | 'graph-tag',
         'prefix': '',
         'timestamp': unixepoch, # from time.time()
         'data': variant, # data for the 'type' graph
        }
        """
        if data['filename'] in glob(os.path.join(basedir, graphs_cache, '*')):
            # we'll just return the cached one
            return

        filename = os.path.join(basedir, graphs_cache, data['filename'])
        if data['type'] == 'graph_tag':
            graph_totals(filename, self.data[data['prefix']], data['data'])
        elif data['type'] == 'graph_tag_users':
            graph_tag_users(filename, self.data[data['prefix']], data['data']['tags'], data['data']['users'])

    def load_data(self):
        """
        self.data[prefix] contains data parsed for that particular prefix.
        
        Its structure is as follows:
        
        {
        'counts': {
            '20100912': [total_nodes, total_ways, total_rels],
            'timestamp': [total_nodes, total_ways, total_rels],
        },
        'nodes': {
            '20100912': {
                'user1': count,
                'user2': count,
            },
            'timestamp': {
                ...
            },
        },
        'ways': {
            '20100912': {
                'user1': count,
                'user2': count,
            },
            'timestamp': {
                ...
            },
        },
        'relations': {
            '20100912': {
                'user1': count,
                'user2': count,
            },
            'timestamp': {
                ...
            },
        },
        'xcoords': ['20100912'],
        'ycoords': defaultdict(<type 'dict'>, {
            'key=val': {
                '20100912': defaultdict(<type 'int'>, {
                    'user1': count,
                    'user2': count,
                 })
            },
            'key2=val2': { ... },
        })
        }
        """
        log.info('Loading data')
        self.data = dict()

        prefixes = glob(os.path.join(json_path, '*_*.json'))
        prefixes = set(map(lambda x: os.path.basename(x).split('_')[0], prefixes))
        for pref in prefixes:
            log.debug('Loading data for %s' % pref)
            self.data[pref] = {}
            for i in ['counts', 'nodes', 'ways', 'relations']:
                self.data[pref][i] = {}
            self.data[pref]['xcoords'] = []
            self.data[pref]['ycoords'] = defaultdict(dict)

            for i in sorted(glob(os.path.join(json_path, pref + '_*.json'))):
                if 'positions' in i or 'tags_users' in i:
                    continue

                load = cjson.decode(open(i).readline())
                timestamp = load[0]
                nodes = load[1]
                ways = load[2]
                rels = load[3]
                tags = load[4]

                self.data[pref]['xcoords'].append(timestamp)
                self.data[pref]['nodes'][timestamp] = nodes
                self.data[pref]['ways'][timestamp] = ways
                self.data[pref]['relations'][timestamp] = rels

                l = [nodes, ways, rels]
                self.data[pref]['counts'][timestamp] = []
                for d in l:
                    tmpcount = 0
                    for c in d:
                        tmpcount += int(d[c])

                    self.data[pref]['counts'][timestamp].append(tmpcount)

                for key in tags:
                    for val in tags[key]:
                        date = defaultdict(int)
                        for user in tags[key][val]:
                            date[user] = tags[key][val][user]
                        self.data[pref]['ycoords']["%s=%s" % (key,val)][timestamp] = date

                del l
        log.info('Loading complete')

    def add_to_queue(self, item):
        self.queue.put_nowait(item)

def graph_totals(filename, data, tags):
    if type(tags) != list:
        tags = [tags]
    tags = sorted(filter(None, tags))

    graph = Graph(filename, 'Tag graph')
    for tag in tags:
        yvalues = []
        for key in data['ycoords'][tag]:
            val = 0
            for user in data['ycoords'][tag][key]:
                val += data['ycoords'][tag][key][user]
            yvalues.append(val)
        graph.add_line(tag, data['ycoords'][tag].keys(), yvalues)
    graph.plot()

def graph_tag_users(filename, data, tags, users):
    if type(tags) != list:
        tags = [tags]
    if type(users) != list:
        users = [users]

    tags = sorted(filter(None, tags))
    users = sorted(filter(None, users))

    graph = Graph(filename, tag)
    for tag in tags:
        for user in users:
            user_y = [ data['ycoords'][tag][x][user] for x in sorted(data['ycoords'][tag].keys()) ]
            graph.add_line(user, data['xcoords'], user_y)
    graph.plot()


def exit_routine(self=None, exiting=False):
    global running
    if exiting:
        running = False
#        return
    if self and not running:
        self.stop()
    if not running:
        sys.exit(0)
    return running

def set_logging():
    global log
    log = logging.getLogger('graph')
    log.setLevel(logging.INFO)
    logh = logging.StreamHandler()
    logh.setLevel(logging.INFO)
    logfmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logh.setFormatter(logfmt)
    log.addHandler(logh)

if __name__ == '__main__':
    set_logging()
    daemon = GraphDaemon()
    daemon.start()

