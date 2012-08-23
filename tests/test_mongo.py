# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import subprocess
import unittest
#from multiprocessing import Process
from mongobag import Connection
from mongobag import NoResultFound


log = logging.getLogger(__name__)


class TestMongoModule(unittest.TestCase):

    def setUp(self):
        #self.mongod = Process(target=self.start_mongo_server)
        #self.mongod.start()
        self.connection = None
        self.connection = Connection(auto_start_request=False)
        self.connection = Connection(auto_start_request=False)
        self.connection.start_request()
        self.database_name = 'test'
        self.database = self.connection[self.database_name]

    def tearDown(self):
        self.connection.drop_database(self.database_name)
        self.connection.end_request()
        self.connection.close()
        #self.mongod.terminate()

    def start_mongo_server(self):
        #mongod run --config /usr/local/etc/mongod.conf
        args = ['mongod', 'run', '--config', '/usr/local/etc/mongod.conf']
        subprocess.call(args)

    def test_insert(self):
        from .model import Account
        from mongobag import get_cls_collection
        from bson.objectid import ObjectId

        account = Account(name='MyName', surname='My Surname',
                          username='MyUsername', password='MyPassword')

        collection = self.database[get_cls_collection(Account)]
        collection.insert(account)
        self.assertEqual(isinstance(account._id, ObjectId), True)
        self.assertEqual(account, collection.find_one(account))

    def test_update(self):
        from .model import Account
        from mongobag import get_cls_collection

        account = Account(name='MyName', surname='My Surname',
                          username='MyUsername', password='MyPassword')

        collection = self.database[get_cls_collection(Account)]
        collection.insert(account)
        account.name = 'My New Name'
        account.surname = 'My New Surname'
        account.username = 'MyNewUsername'
        account.password = 'MyNewPassword'
        collection.update(Account._id == account._id, account)
        self.assertEqual(account, collection.find_one(Account._id == account._id))

    def test_save(self):
        from .model import Account
        from mongobag import get_cls_collection
        from bson.objectid import ObjectId

        account = Account(name='MyName', surname='My Surname',
                          username='MyUsername', password='MyPassword')

        collection = self.database[get_cls_collection(Account)]
        self.assertEqual(account._id, None)
        collection.save(account)
        self.assertEqual(isinstance(account._id, ObjectId), True)
        old_account = Account(**account.asdict())
        account.name = 'My New Name'
        account.surname = 'My New Surname'
        account.username = 'MyNewUsername'
        account.password = 'MyNewPassword'
        collection.save(account)
        self.assertEqual(account, collection.find_one(Account._id == account._id))
        self.assertNotEqual(account, old_account)

    def test_find_one(self):
        from .model import Account
        from mongobag import get_cls_collection
        collection = self.database[get_cls_collection(Account)]
        self.assertRaises(NoResultFound, collection.find_one, Account._id == 'No ID')

    def test_find(self):
        from .model import Account
        from mongobag import get_cls_collection
        from bson.objectid import ObjectId

        account = Account(name='My Name', surname='My Surname',
                          username='MyUsername', password='MyPassword')

        collection = self.database[get_cls_collection(Account)]
        collection.insert(account)
        self.assertEqual(isinstance(account._id, ObjectId), True)
        new_account = Account(name='My New Name', surname='My New Surname',
                              username='MyNewUsername', password='MyNewPassword')
        collection.save(new_account)
        self.assertEqual(collection.find().count(), 2)
        self.assertEqual(collection.find(Account.name == 'My Name')[0], account)
        self.assertEqual(collection.find(Account.name == 'My New Name')[0],
                         new_account)
