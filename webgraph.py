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
from glob import glob

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

def check_prefix(prefix):
    path = os.path.join(html_path, '%s_*' % prefix)
    if len(glob(path)) == 0:
        abort(404, 'No data available for %s' % prefix)

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
@route('/stats/:prefix')
def stats(prefix=default_prefix):
    check_prefix(prefix)
    return open(os.path.join(html_path, "%s_stats.html" % prefix))

@route('/stats/:prefix/:key')
def show_key(prefix, key):
    check_prefix(prefix)
    if key == 'full':
        # TODO: more explicative message
        return "Nothing here, really."
    return open(os.path.join(html_path, "%s_%s.html" % (prefix, sanitize(key))))

@route('/stats/full/:prefix/:key')
@route('/stats/full/:prefix/:key/:value')
def show_full(prefix, key, value=None):
    check_prefix(prefix)
    if not value:
        if key in ['nodes', 'ways', 'relations']:
            return open(os.path.join(html_path, "%s_%s_full.html" % (prefix, key)))
        else:
            # TODO: show a <ul> of available tags
            return "You're trying to do what?"
    return open(os.path.join(html_path, "%s_%s=%s_full.html" % (prefix, sanitize(key), sanitize(value))))

@route('/user/:prefix/:user')
def show_user(prefix, user):
    check_prefix(prefix)

    bottle.TEMPLATES.clear()

    from urllib2 import unquote, urlopen, quote
    try:
        userfile = sanitize(unquote(user)).replace(' ', '_')
        f = open(os.path.join(profiles_path, '%s_%s.json' % (prefix, userfile)))
        primitives, tags = cjson.decode(f.readline())
        f.close()
    except IOError:
        abort(404, 'User profile not found')
    else:
        imgurl = 'http://www.openstreetmap.org/user/%s' % quote(user)
        print imgurl
        for line in urlopen(imgurl):
            if 'user_image' in line:
                # <img alt="Primopiano" class="user_image" src="/user/image/71261/primopiano.jpg?1271701916" style="float: right" />
                imgurl = 'http://www.openstreetmap.org' + line.split('src="')[1].split('"')[0]
                break

        tmpl = template(open(os.path.join(templates_path, 'user.tmpl')))
        out = tmpl.generate(
            imgurl=imgurl,
            user=user,
            primitives=primitives,
            tags=tags,
        )
        return out.render('xhtml')

###
# Graphs
###
@route('/graphs')
@route('/graphs/:prefix')
def graphs(prefix=default_prefix):
    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    bottle.TEMPLATES.clear()
    tmpl = template(open("views/webgraph.tmpl"))
    out = tmpl.generate(
        tags=get_tags(prefix=get_prefix(request))["r"],
        users=get_users(prefix=get_prefix(request))["r"],
    )
    return out.render('xhtml')

@route('/get/tags')
@route('/get/tags/:prefix')
def get_tags(prefix=default_prefix):
    check_prefix(prefix)
    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    return {"r":sorted(tags)}

@route('/get/tags/:prefix/:user')
def get_tags_for(prefix, user):
    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    counts, xcoords, ycoords = parse_json(prefix)
    tags = set()
    for tag in ycoords:
        for date in ycoords[tag]:
            if ycoords[tag][date].has_key(user):
                tags.add(tag)
                break
    return {"r":sorted(list(tags))}

@route('/get/users')
@route('/get/users/:prefix')
def get_users(prefix=default_prefix):
    check_prefix(prefix)
    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    return {"r":sorted(users)}

@route('/get/users/:prefix/:tag')
def get_users_for(prefix, tag):
    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    counts, xcoords, ycoords = parse_json(prefix)
    users = set()
    for date in ycoords[tag].values():
        users.update(date.keys())
    return {"r":sorted(list(users))}

@get('/graph-tag-user/:prefix')
def graph_tag_user(prefix=default_prefix):
    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    bottle.response.set_content_type("image/svg+xml; charset=UTF-8")
    counts, xcoords, ycoords = parse_json(prefix)
    filename = graph_tag_users(prefix, request.GET["tag"], request.GET.getall("user"))[0]
    return static_file(os.path.basename(filename), graphs_cache, mimetype="image/svg+xml; charset=UTF-8")

@get('/graph-tag/:prefix')
def graph_tag(prefix=default_prefix):
    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    bottle.response.set_content_type('image/svg+xml; charset=UTF-8')
    counts, xcoords, ycoords = parse_json(prefix)
    filename = graph_totals(prefix, request.GET.getall('tag'))
    return static_file(os.path.basename(filename), graphs_cache, mimetype='image/svg+xml; charset=UTF-8')

##
# Source
##
@route('/source')
def go_to_source():
    redirect('http://bugs.hanskalabs.net/projects/osm-stats/repository')

##
# Bugs
##
@route('/bugs')
def go_to_bugs():
    redirect('http://bugs.hanskalabs.net/projects/osm-stats/issues')

##
# Credits
##
@route('/credits')
def credits():
    tmpl = template(open("views/credits.tmpl"))
    out = tmpl.generate()
    return out.render('xhtml')


bottle.debug(True)
#bottle.default_app().autojson = True
#run(host=host_ip_addr, port=8080, reloader=True)

application = bottle.default_app()
