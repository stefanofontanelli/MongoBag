# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import subprocess
import unittest
from multiprocessing import Process
from pymongo import Connection
from pymongo.errors import AutoReconnect
from pymongo.errors import ConnectionFailure


log = logging.getLogger(__name__)

"""
class TestMongoBase(unittest.TestCase):

    def setUp(self):
        self.mongod = Process(target=self.start_mongo_server)
        self.mongod.start()
        self.connection = None
        while(self.connection is None):
            try:
                self.connection = Connection(auto_start_request=False)
            except (AutoReconnect, ConnectionFailure):
                continue
            else:
                self.connection.start_request()

        self.database_name = 'test'
        self.database = self.connection[self.database_name]

    def tearDown(self):
        self.connection.drop_database(self.database_name)
        self.connection.end_request()
        self.connection.close()
        self.mongod.terminate()

    def start_mongo_server(self):
        #mongod run --config /usr/local/etc/mongod.conf
        args = ['mongod', 'run', '--config', '/usr/local/etc/mongod.conf']
        subprocess.call(args)

    def test_crud(self):
        from model import Account
        from mongobag import MongoBase
        from mongobag import get_obj_collection
        from mongobag import NoResultFound

        ctrl = MongoBase(Account, self.database)
        account = ctrl.create(name='My Name',
                              surname='My Surname',
                              username='My Username',
                              password='My Password')
        obj = get_obj_collection(account).find_one()
        self.assertEqual(account._id, obj['_id'])
        # Test MongoBase().read
        obj = ctrl.read(Account._id == account._id, self.database)
        self.assertEqual(account._id, obj._id)
        # Test MongoBase().update
        obj = account.serialize()
        obj['name'] = 'My New Name'
        obj['surname'] = 'My New Surname'
        obj = ctrl.update(**obj)
        self.assertEqual(account._id, obj._id)
        self.assertNotEqual(account.name, obj.name)
        self.assertNotEqual(account.surname, obj.surname)
        self.assertEqual(account.username, obj.username)
        self.assertEqual(account.password, obj.password)
        doc = get_obj_collection(obj).find_one()
        self.assertEqual(obj._id, doc['_id'])
        ctrl.delete(self.database, **doc)
        self.assertRaises(NoResultFound, ctrl.read, Account._id == doc['_id'], self.database)
"""
