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

import os
import sys

mydir = os.path.dirname(__file__)
os.chdir(mydir)
sys.path.append(mydir)

import bottle
from bottle import *
from plot import *
from genshi.template import MarkupTemplate as template
import cjson

from helpers import *
from config import *

@route('/')
def index():
    bottle.TEMPLATES.clear()
    return open(os.path.join(html_path, 'index.html'))

def workinprogress(reason=''):
    tmpl = template(open("views/workinprogress.tmpl"))
    out = tmpl.generate(
        reason=reason
    )
    return out.render('xhtml')

# included files
@route('/js/:f')
def send_js(f):
    return static_file(f, 'js', mimetype="text/javascript")

@route('/img/:f')
def send_img(f):
    return static_file(f, 'img')

@route('/fonts/:f')
def send_font(f):
    return static_file(f, 'fonts')

@route('/style/:f')
def send_style(f):
    return static_file(f, 'style', mimetype='text/css')

###
# Stats
###
@route('/stats')
@route('/stats/')
def stats():
    prefix = get_prefix(request)
    if request.GET.get('full'):
        filename = '%s_stats_full.html' % prefix
    else:
        filename = "%s_stats.html" % prefix
    return open(os.path.join(html_path, filename))

@route('/stats/:key/')
@route('/stats/:key')
def show_key(key):
    prefix = get_prefix(request)
    if request.GET.get('full'):
        filename = '%s_%s_full.html' % (prefix, sanitize(key))
    else:
        filename = '%s_%s.html' % (prefix, sanitize(key))
    return open(os.path.join(html_path, filename))

###
# Graphs
###
@route('/graphs/')
@route('/graphs')
def graphs():
    return workinprogress('Temporary disabled due to performance issues')
    bottle.TEMPLATES.clear()
    tmpl = template(open("views/webgraph.tmpl"))
    out = tmpl.generate(
        tags=get_tags(prefix=get_prefix(request))["r"],
        users=get_users(prefix=get_prefix(request))["r"],
    )
    return out.render('xhtml')

@route('/get/tags')
def get_tags(prefix=None):
    if not prefix:
        prefix = get_prefix(request)
    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    return {"r":sorted(tags)}

@route('/get/tags/:user')
def get_tags_for(user, prefix=None):
    return workinprogress('Temporary disabled due to performance issues')
    if not prefix:
        prefix = get_prefix(request)

    counts, xcoords, ycoords = parse_json(prefix)
    tags = set()
    for tag in ycoords:
        for date in ycoords[tag]:
            if ycoords[tag][date].has_key(user):
                tags.add(tag)
                break
    return {"r":sorted(list(tags))}

@route('/get/users')
def get_users(prefix=None):
    if not prefix:
        prefix = get_prefix(request)

    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    return {"r":sorted(users)}

@route('/get/users/:tag')
def get_users_for(tag, prefix=None):
    return workinprogress('Temporary disabled due to performance issues')
    if not prefix:
        prefix = get_prefix(request)

    counts, xcoords, ycoords = parse_json(prefix)
    users = set()
    for date in ycoords[tag].values():
        users.update(date.keys())
    return {"r":sorted(list(users))}

@get('/graph-tag-user')
def graph_tag_user(prefix=None):
    return workinprogress('Temporary disabled due to performance issues')
    if not prefix:
        prefix = get_prefix(request)

    bottle.response.set_content_type("image/svg+xml; charset=UTF-8")
    counts, xcoords, ycoords = parse_json(prefix)
    filename = graph_tag_users(prefix, request.GET["tag"], request.GET.getall("user"))[0]
    return static_file(os.path.basename(filename), graphs_cache, mimetype="image/svg+xml; charset=UTF-8")

@get('/graph-tag')
def graph_tag(prefix=None):
    return workinprogress('Temporary disabled due to performance issues')
    if not prefix:
        prefix = get_prefix(request)

    bottle.response.set_content_type('image/svg+xml; charset=UTF-8')
    counts, xcoords, ycoords = parse_json(prefix)
    filename = graph_totals(prefix, request.GET.getall('tag'))
    return static_file(os.path.basename(filename), graphs_cache, mimetype='image/svg+xml; charset=UTF-8')

##
# Source
##
@route('/source')
@route('/source/')
def go_to_source():
    redirect('http://bugs.hanskalabs.net/projects/osm-stats/repository')

##
# Bugs
##
@route('/bugs')
@route('/bugs/')
def go_to_bugs():
    redirect('http://bugs.hanskalabs.net/projects/osm-stats/issues')

##
# Credits
##
@route('/credits')
@route('/credits/')
def credits():
    tmpl = template(open("views/credits.tmpl"))
    out = tmpl.generate()
    return out.render('xhtml')


bottle.debug(True)
#bottle.default_app().autojson = True
#run(host=host_ip_addr, port=8080, reloader=True)

application = bottle.default_app()
