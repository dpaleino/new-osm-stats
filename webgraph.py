#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle
from bottle import *
from plot import graph_tag_users, parse_json
from genshi.template import MarkupTemplate as template
import os

@route('/')
def index():
    bottle.TEMPLATES.clear()
    tmpl = template(open("views/webgraph.tmpl"))
    out = tmpl.generate(
        tags=get_tags()["r"],
    )
    return out.render('xhtml')

@route('/get/tags')
def get_tags():
    counts, xcoords, ycoords = parse_json()
    return {"r":sorted(ycoords.keys())}

@route('/get/users/:tag')
def get_users(tag):
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
    return static_file(os.path.basename(filename), "/tmp/", mimetype="image/svg+xml; charset=UTF-8")

@route('/js/:f')
def send_js(f):
    return static_file(f, "js/", mimetype="text/javascript")

if __name__ == "__main__":
    bottle.debug(True)
    bottle.default_app().autojson = True
    run(host='192.168.1.33', port=8080, reloader=False)
