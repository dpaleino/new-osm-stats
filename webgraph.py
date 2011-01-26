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
from genshi.template import TemplateLoader
from genshi.filters import Translator
import gettext
from genshi.template import MarkupTemplate as template
import cjson
from glob import glob
import cPickle as pickle
import time

from helpers import *
from config import *

linguas = map(lambda x: x.strip(), open(os.path.join(po_path, 'LINGUAS')).readlines())
langs = {}
for l in linguas:
    langs[l] = gettext.translation('messages', locale_path, languages=[l])
langs[default_lang].install()
loader = TemplateLoader(templates_path, callback=lambda x: Translator(langs[default_lang]).setup(x))

def check_lang():
    global langs, loader

    chosen = request.get_cookie('lang')
    if chosen:
        if chosen not in linguas:
            chosen = default_lang
    else:
        try:
            oklangs = request.environ['HTTP_ACCEPT_LANGUAGE'].split(',')
            oklangs = map(lambda x: x.split('-')[0].split(';')[0], oklangs)
            for l in oklangs:
                if l in linguas:
                    chosen = l
                    break
        except KeyError:
            chosen = default_lang

    langs[chosen].install()
    loader = TemplateLoader(templates_path, callback=lambda x: Translator(langs[chosen]).setup(x))

def workinprogress(reason=''):
    check_lang()
    tmpl = loader.load("workinprogress.tmpl")
    out = tmpl.generate(
        reason=reason
    )
    return out.render('xhtml')

def check_prefix(prefix):
    path = os.path.join(pickle_path, '%s_*' % prefix)
    if len(glob(path)) == 0:
        abort(404, 'No data available for %s' % prefix)

def data(name):
    f = open(os.path.join(pickle_path, name))
    ret = pickle.load(f)
    f.close()
    return ret

@route('/lang/:locale')
def set_lang(locale):
    response.set_cookie('lang', locale, path='/', expires=+500)
    try:
        redirect(request.environ['HTTP_REFERER'])
    except KeyError:
        redirect('/')

@route('/')
def index():
    bottle.TEMPLATES.clear()
    check_lang()
    return loader.load('index.tmpl').generate().render('xhtml')

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
    check_lang()
    tmpl = loader.load('statistiche.tmpl')
    out = tmpl.generate(**data("%s_stats.pickle" % prefix))
    return out.render('xhtml')

@route('/stats/:prefix/:key')
def show_key(prefix, key):
    check_prefix(prefix)
    check_lang()
    if key == 'full':
        # TODO: more explicative message
        return "Nothing here, really."
    tmpl = loader.load('key.tmpl')
    out = tmpl.generate(**data("%s_%s.pickle" % (prefix, sanitize(key))))
    return out.render('xhtml')

@route('/stats/full/:prefix/:key')
@route('/stats/full/:prefix/:key/:value')
def show_full(prefix, key, value=None):
    check_prefix(prefix)
    check_lang()
    if not value:
        if key in ['nodes', 'ways', 'relations']:
            tmpl = loader.load('table.tmpl')
            out = tmpl.generate(**data("%s_%s_full.pickle" % (prefix, key)))
            return out.render('xhtml')
        else:
            # TODO: show a <ul> of available tags
            return "You're trying to do what?"
    tmpl = loader.load('table.tmpl')
    out = tmpl.generate(**data("%s_%s=%s_full.pickle" % (prefix, sanitize(key), sanitize(value))))
    return out.render('xhtml')

@route('/user/:prefix/:user')
def show_user(prefix, user):
    check_prefix(prefix)
    check_lang()

    bottle.TEMPLATES.clear()

    from urllib2 import unquote, urlopen, quote, HTTPError
    try:
        userfile = sanitize(unquote(user)).replace(' ', '_')
        f = open(os.path.join(profiles_path, '%s_%s.json' % (prefix, userfile)))
        primitives, tags = cjson.decode(f.readline())
        f.close()
    except IOError:
        abort(404, 'User profile not found')
    else:
        imgurl = 'http://www.openstreetmap.org/user/%s' % quote(user)
        try:
            stream = urlopen(imgurl)
            for line in stream:
                if 'user_image' in line:
                    # <img alt="Primopiano" class="user_image" src="/user/image/71261/primopiano.jpg?1271701916" style="float: right" />
                    imgurl = 'http://www.openstreetmap.org' + line.split('src="')[1].split('"')[0]
                    break
        except HTTPError:
            imgurl = '#'

        tmpl = loader.load('user.tmpl')
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
#    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    check_lang()
    bottle.TEMPLATES.clear()
    tmpl = loader.load("webgraph.tmpl")
    out = tmpl.generate(
        tags=get_tags(prefix)["r"],
        users=get_users(prefix)["r"],
        prefix=prefix,
    )
    return out.render('xhtml')

@route('/get/tags')
@route('/get/tags/:prefix')
def get_tags(prefix=default_prefix):
    check_prefix(prefix)
    check_lang()
    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    t = defaultdict(list)
    for i in tags:
        key, val = i.split('=', 1)
        t[key].append(val)
    if 'q' in request.GET:
        return '\n'.join(sorted([x for x in tags if x.lower().startswith(request.GET['q'])]))
    else:
        return {"r": dict(t)}

@route('/get/tags/:prefix/:user')
def get_tags_for(prefix, user):
#    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    check_lang()
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
    check_lang()
    tags, users = cjson.decode(open(os.path.join(json_path, '%s_tags_users.json' % prefix)).readline())
    if 'q' in request.GET:
        return '\n'.join(sorted([x for x in users if x.lower().startswith(request.GET['q'])]))
    else:
        return {"r":sorted(users)}

@route('/get/users/:prefix/:tag')
def get_users_for(prefix, tag):
    check_prefix(prefix)
    check_lang()

    d = pickle.load(open(os.path.join(basedir, graphs_outdir, prefix + '_tagusers.pickle')))
    if 'q' in request.GET:
        return '\n'.join(sorted([x for x in d[tag] if x.lower().startswith(request.GET['q'])]))
    else:
        return {"r": d[tag]}

@route('/get/graph/:filename')
def get_graph_file(filename):
    bottle.response.set_content_type("image/svg+xml; charset=UTF-8")
    return static_file(filename, graphs_cache, mimetype="image/svg+xml; charset=UTF-8")

@get('/graph-tag-user/:prefix')
def graph_tag_user(prefix=default_prefix):
    check_prefix(prefix)
    check_lang()

    tag = request.GET.get('tag')
    users = sorted(request.GET.getall('user[]'))
    filename = hashlib.md5(repr([prefix, tag, users])).hexdigest()
    data = dict(
        filename=filename + '.svg',
        type='graph_tag_users',
        prefix=prefix,
        timestamp=time.time(),
        data=dict(tag=tag,
                users=users,
            ),
    )
    pickle.dump(data, open(os.path.join(basedir, graphs_cmddir, filename), 'w'), protocol=2)
    time.sleep(1)
    return '%s.svg' % filename

@get('/graph-tag/:prefix')
def graph_tag(prefix=default_prefix):
#    return workinprogress('Temporary disabled due to performance issues')

    check_prefix(prefix)
    check_lang()

    tags = request.GET.getall('tag[]')
    filename = hashlib.md5(repr([prefix, tags])).hexdigest()
    data = dict(
        filename=filename + '.svg',
        type='graph_tag',
        prefix=prefix,
        timestamp=time.time(),
        data=tags,
    )
    pickle.dump(data, open(os.path.join(basedir, graphs_cmddir, filename), 'w'), protocol=2)
    time.sleep(1)
    return '%s.svg' % filename

@get('/graph-nodes')
@get('/graph-nodes/:prefix')
@get('/graph-ways')
@get('/graph-ways/:prefix')
@get('/graph-relations')
@get('/graph-relations/:prefix')
def graph_primitive(prefix=default_prefix):
    action = request.url.split('/')[3]

    data = dict(
        type='graph_primitive',
        prefix=prefix,
        timestamp=time.time(),
    )

    filename = prefix + '_'
    if 'nodes' in action:
        filename += 'nodes'
        data['data'] = 'nodes'
    elif 'ways' in action:
        filename += 'ways'
        data['data'] = 'ways'
    elif 'relations' in action:
        filename += 'relations'
        data['data'] = 'relations'

    if request.GET.getall('user[]'):
        data['type'] = 'graph_user_primitive'
        what = data['data']
        users = sorted(set(request.GET.getall('user[]')))
        data['data'] = [what, users]
        filename = hashlib.md5(repr([prefix, what, users])).hexdigest()

    data['filename'] = filename + '.svg'
    pickle.dump(data, open(os.path.join(basedir, graphs_cmddir, filename), 'w'), protocol=2)
    time.sleep(1)
    return '%s.svg' % filename

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
    check_lang()
    tmpl = loader.load("credits.tmpl")
    out = tmpl.generate()
    return out.render('xhtml')


bottle.debug(True)
#bottle.default_app().autojson = True
#run(host=host_ip_addr, port=8080, reloader=True)

application = bottle.default_app()
