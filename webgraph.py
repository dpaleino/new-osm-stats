#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle
from bottle import *
from plot import graph_tag_users, parse_json
from plot import graphs_path, graphs_cache
from genshi.template import MarkupTemplate as template
from fast_stats import html_path
import os

from helpers import *

os.chdir(os.path.dirname(__file__))

@route('/')
def index():
    bottle.TEMPLATES.clear()
    return open(os.path.join(html_path, 'index.html'))

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

@route('/stats/')
@route('/stats/:filename')
def stats(filename=None):
    prefix = "italy"
    if request.GET.get('prefix'):
        prefix = str(sanitize(request.GET['prefix']))
    if not filename:
        filename = "%s_stats.html" % prefix
    return open(os.path.join(html_path, filename))

@route('/graphs')
def graphs():
    bottle.TEMPLATES.clear()
    tmpl = template(open("views/webgraph.tmpl"))
    out = tmpl.generate(
        tags=get_tags()["r"],
        users=get_users()["r"],
    )
    return out.render('xhtml')

@route('/get/tags')
def get_tags():
    counts, xcoords, ycoords = parse_json()
    return {"r":sorted(ycoords.keys())}

@route('/get/tags/:user')
def get_tags_for(user):
    counts, xcoords, ycoords = parse_json()
    tags = set()
    for tag in ycoords:
        for date in ycoords[tag]:
            if ycoords[tag][date].has_key(user):
                tags.add(tag)
                break
    return {"r":sorted(list(tags))}

@route('/get/users')
def get_users():
    nodes, ways, rels, xcoords, ycoords = parse_json(full=True)
    users = set()
    for tag in ycoords.keys():
        for date in ycoords[tag]:
            users.update(ycoords[tag][date].keys())

    return {"r":sorted(list(users))}

@route('/get/users/:tag')
def get_users_for(tag):
    counts, xcoords, ycoords = parse_json()
    users = set()
    for date in ycoords[tag].values():
        users.update(date.keys())
    return {"r":sorted(list(users))}

@get('/graph')
def graph():
    bottle.response.set_content_type("image/svg+xml; charset=UTF-8")
    counts, xcoords, ycoords = parse_json()
    filename = graph_tag_users(request.GET["tag"], request.GET["user"])[0]
    return static_file(os.path.basename(filename), graphs_cache, mimetype="image/svg+xml; charset=UTF-8")

bottle.debug(True)
bottle.default_app().autojson = True
run(host='192.168.1.33', port=8080, reloader=True)

application = bottle.default_app()
