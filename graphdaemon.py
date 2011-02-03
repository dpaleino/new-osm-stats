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

import db
from sqlalchemy import *

running = True
log = None

class PE(pyinotify.ProcessEvent):
    def __init__(self, main):
        pyinotify.ProcessEvent.__init__(self)
        self.main = main

    def process_IN_CLOSE_WRITE(self, event):
        self.main.add_to_queue(event)

class GraphDaemon(object):
    def __init__(self):
        self.daemonize()
        self.queue = Queue()
        self.notifier = None

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
        fout = open(os.path.join(basedir, graphs_logdir, 'out'), 'a+')
        ferr = open(os.path.join(basedir, graphs_logdir, 'err'), 'a+', 0)
        os.dup2(fin.fileno(), sys.stdin.fileno())
        os.dup2(fout.fileno(), sys.stdout.fileno())
        os.dup2(ferr.fileno(), sys.stderr.fileno())

    def start(self):
        threading.Thread(None, self.loop).start()

        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(wm, PE(self))
        wm.add_watch(os.path.join(basedir, graphs_cmddir), pyinotify.IN_CLOSE_WRITE, rec=True)
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
            fn = graph_totals
        elif data['type'] == 'graph_tag_users':
            fn = graph_tag_users
        elif data['type'] == 'graph_primitive':
            fn = graph_primitive
        elif data['type'] == 'graph_user_primitive':
            fn = graph_user_primitive
        fn(filename, data)

    def add_to_queue(self, item):
        self.queue.put_nowait(item)

def graph_totals(filename, data):
    tags = data['data']
    db.load_db(data['prefix'])

    if type(tags) != list:
        tags = [tags]
    tags = sorted(filter(None, tags))

    graph = Graph(filename, 'Tag graph')
    for tag in tags:
        ycoords = []

        key, value = tag.split('=')
        table = Table(key, db.meta, autoload=True)
        dates = list(db.run(select([table.c.date]).distinct().where(table.c.value == value)))
        xcoords = zip(*dates)[0]

        # FIXME: there's sqlalchemy.func.sum()
        for d in xcoords:
            counts = list(db.run(select([table.c.count]).where(and_(table.c.date == d, table.c.value == value))))
            val = sum(zip(*counts)[0])
            ycoords.append(val)

        graph.add_line(tag, xcoords, ycoords)
    graph.plot()

def graph_tag_users(filename, data):
    users = data['data']['users']
    tag = data['data']['tag']
    key, value = tag.split('=')
    db.load_db(data['prefix'])

    if type(users) != list:
        users = [users]

    users = sorted(filter(None, users))

    table = Table(key, db.meta, autoload=True)

    graph = Graph(filename, tag)
    for user in users:
        results = list(db.run(select(columns=[table.c.date, table.c.count]).where(and_(table.c.username == user, table.c.value == value))))
        xcoords, ycoords = zip(*results)
        graph.add_line(user, xcoords, ycoords)
    graph.plot()

def graph_primitive(filename, data):
    what = data['data']

    db.load_db(data['prefix'])
    table = Table(what, db.meta, autoload=True)

    graph = Graph(filename, what.capitalize())
    ycoords = []
    dates = list(db.run(select([table.c.date]).distinct()))
    xcoords = zip(*dates)[0]
    for d in xcoords:
        counts = list(db.run(select([table.c.count]).where(table.c.date == d)))
        ycoords.append(sum(zip(*counts)[0]))
    graph.add_line(what.capitalize(), xcoords, ycoords)
    graph.plot()

def graph_user_primitive(filename, data):
    what, users = data['data']
    db.load_db(data['prefix'])

    if type(users) != list:
        users = [users]
    users = sorted(filter(None, users))

    table = Table(what, db.meta, autoload=True)

    graph = Graph(filename, 'Comparison for %s' % what)
    for user in users:
        results = list(db.run(select(columns=[table.c.date, table.c.count]).where(table.c.username == user)))
        xcoords, ycoords = zip(*results)
        graph.add_line(user, xcoords, ycoords)
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

