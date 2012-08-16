# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import unittest


log = logging.getLogger(__name__)


class TestFields(unittest.TestCase):

    def test_field_default_callable(self):
        pass

    def test_field_missing_callable(self):
        pass

    def test_object_id(self):
        from mongobag import ObjectId
        import bson
        import colander

        field = ObjectId()
        field.name = '_id'
        self.assertEqual(field.serialize(), colander.null)
        self.assertEqual(field.deserialize(), colander.null)

        objectid = bson.objectid.ObjectId('x' * 12)
        self.assertEqual(field.serialize(objectid), objectid)
        self.assertEqual(field.deserialize(objectid), objectid)
        self.assertRaises(colander.Invalid, field.serialize, '')
        self.assertRaises(colander.Invalid, field.serialize, {'_id': objectid})
        self.assertRaises(colander.Invalid, field.deserialize, '')
        self.assertRaises(colander.Invalid, field.deserialize, {'_id': objectid})

        for i in xrange(0, 12):
            self.assertRaises(colander.Invalid, field.deserialize, 'x' * i)
        for i in xrange(13, 32):
            self.assertRaises(colander.Invalid, field.deserialize, 'x' * i)

        self.assertEqual(str(field.deserialize('x' * 12)), str(objectid))

    def test_integer(self):
        from mongobag import Integer
        import colander

        field = Integer(name='myfield')
        self.assertEqual(field.serialize(), colander.null)
        self.assertRaises(colander.Invalid, field.deserialize)
        self.assertEqual(field.deserialize(5), 5)
        self.assertEqual(field.deserialize(5.0), 5)
        self.assertRaises(colander.Invalid, field.deserialize, '5.0')
        self.assertRaises(colander.Invalid, field.deserialize, '')
        self.assertRaises(colander.Invalid, field.deserialize, 'a string')

    def test_string(self):
        from mongobag import String

        field = String()
        value = 'pippo'
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_boolean(self):
        from mongobag import Boolean

        field = Boolean()
        value = True
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_float(self):
        from mongobag import Float

        field = Float()
        value = 9.99
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_date(self):
        from mongobag import Date
        import datetime

        field = Date()
        value = datetime.date.today()
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_datetime(self):
        from mongobag import DateTime
        import datetime

        field = DateTime()
        value = datetime.datetime.now()
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_time(self):
        from mongobag import Time
        import datetime

        field = Time()
        value = datetime.datetime.now().time()
        self.assertEqual(field.serialize(value), value)
        self.assertEqual(field.deserialize(value), value)

    def test_embedded(self):
        from mongobag import Embedded
        from model import DummyDocument

        field = Embedded(DummyDocument)
        value = DummyDocument(name='Dummy Document')
        params = dict(name=value.name)
        self.assertEqual(field.serialize(value), params)
        self.assertEqual(field.deserialize(value), value)
        self.assertEqual(field.serialize(field.deserialize(params)), params)

    def test_embedded_list(self):
        from mongobag import EmbeddedList
        from model import DummyDocument

        field = EmbeddedList(DummyDocument)
        doc = DummyDocument(name='Dummy Document')
        value = [doc, doc, doc]
        serialized = dict(name=doc.name)
        list_ = [serialized, serialized, serialized]
        self.assertEqual(field.serialize(value), list_)
        self.assertEqual(field.deserialize(value), value)
        self.assertEqual(field.serialize(field.deserialize(list_)), list_)


class TestDocument(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_metaclass_setattr(self):
        from model import MainDocument
        from mongobag import String
        self.assertRaises(AttributeError, setattr, MainDocument, 'string', String())

    def test_document_serialize(self):
        from model import DummyDocument
        value = DummyDocument(name='Dummy Document')
        self.assertEqual(value.serialize(), {'name': value.name})

    def test_get_document_registry(self):
        from model import DummyDocument
        from mongobag import get_document_registry
        get_document_registry(DummyDocument)

    def test_get_document_schema(self):
        from model import DummyDocument
        from mongobag import get_document_registry
        get_document_registry(DummyDocument)

    def test_document_init(self):
        from model import MainDocument
        import colander
        import datetime
        self.assertEqual(getattr(MainDocument, MainDocument._DATABASE), None)
        self.assertEqual(getattr(MainDocument, MainDocument._COLLECTION),
                         'maindocument')
        self.assertEqual(getattr(MainDocument, MainDocument._VALIDATOR), None)
        params = dict()
        self.assertRaises(colander.Invalid, MainDocument, **params)
        params = dict(integer=5,
                      string='teststring',
                      boolean=False,
                      float=0.5,
                      decimal=0.5,
                      datetime=datetime.datetime.now(),
                      date=datetime.date.today(),
                      time=datetime.datetime.now().time(),
                      colander='colander.Invalid')
        self.assertRaises(TypeError, MainDocument, **params)
        params = dict(integer=5,
                      string='teststring',
                      boolean=False,
                      float=0.5,
                      datetime=datetime.datetime.now(),
                      date=datetime.date.today(),
                      time=datetime.datetime.now().time())
        doc = MainDocument(**params)
        self.assertEqual(doc.string, params['string'])
        self.assertRaises(colander.Invalid, setattr, doc, 'integer', 'astring')

    def test_document_mongoq_queries(self):
        from model import MainDocument
        id_ = '1234567890AB'
        self.assertEqual(MainDocument._id != id_, {'attr': {'$ne': id_}})
