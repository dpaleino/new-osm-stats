#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2011, David Paleino <d.paleino@gmail.com>
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

from sqlalchemy import *
from sqlalchemy.exc import *
from config import default_prefix, db_path
import os

db = None
meta = None

def load_db(prefix):
    global db, meta
    db = create_engine('sqlite:///' + os.path.join(db_path, prefix) + '_osmstats.sqlite')
    meta = MetaData(db)

load_db(default_prefix)

def init():
    for name in ['nodes', 'ways', 'relations']:
        table = Table(name, meta,
            Column('date', Integer, nullable=False),
            Column('username', String(60), nullable=False),
            Column('count', Integer, nullable=False),
            Column('position', Integer, nullable=False),
        )
        table.create()

def run(statement):
    """Executes a sqlalchemy statement"""
    return statement.execute()

def make_table(name):
    table = Table(name, meta,
        #Column('id', Integer, primary_key=True),
        Column('value', String(20), nullable=False),
        Column('date', Integer, nullable=False),
        Column('username', String(60), nullable=False),
        Column('count', Integer, nullable=False),
        Column('position', Integer, nullable=False),
    )

    try:
        table.create()
    except OperationalError:
        pass

if __name__ == '__main__':
    import sys
    make_table(sys.argv[1])
