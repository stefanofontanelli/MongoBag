# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import unittest


log = logging.getLogger(__name__)


class TestFields(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def check_field(self, field):
        import colander
        self.assertEqual(field.name, '')
        self.assertEqual(isinstance(field.schema, colander.SchemaNode), True)
        self.assertRaises(AttributeError, setattr, field, 'type', None)
        self.assertRaises(AttributeError, setattr, field, 'schema', None)
        name = "username"
        field.name = name
        self.assertEqual(field.name, name)

    def test_field(self):
        from mongobag import Field
        import colander

        field = Field(colander.String())
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.String), True)
        self.assertRaises(ValueError, Field, colander.SchemaNode)
        name = 'password'
        field = Field(colander.String(), name=name)
        self.assertEqual(field.name, name)

    def test_integer(self):
        from mongobag import Integer
        import colander

        field = Integer()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Integer), True)

    def test_boolean(self):
        from mongobag import Boolean
        import colander

        field = Boolean()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Boolean), True)

    def test_float(self):
        from mongobag import Float
        import colander

        field = Float()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Float), True)

    def test_decimal(self):
        from mongobag import Decimal
        import colander

        field = Decimal()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Decimal), True)

    def test_datetime(self):
        from mongobag import DateTime
        import colander

        field = DateTime()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.DateTime), True)

    def test_date(self):
        from mongobag import Date
        import colander

        field = Date()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Date), True)

    def test_time(self):
        from mongobag import Time
        import colander

        field = Time()
        self.check_field(field)
        self.assertEqual(isinstance(field.type, colander.Time), True)

    def test_global_object(self):
        from mongobag import GlobalObject
        import colander

        self.assertRaises(TypeError, GlobalObject)
        field = GlobalObject(colander)
        self.check_field(field)

    def test_mapping(self):
        from mongobag import Mapping

        self.assertRaises(TypeError, Mapping)
        field = Mapping()
        self.check_field(field)

    def test_tuple(self):
        from mongobag import Tuple

        self.assertRaises(TypeError, Tuple)
        field = Tuple()
        self.check_field(field)

    def test_sequence(self):
        from mongobag import Sequence

        self.assertRaises(TypeError, Sequence)
        field = Sequence()
        self.check_field(field)

    def test_object_id(self):
        from mongobag import ObjectId
        import bson
        import colander

        field = ObjectId()
        self.check_field(field)
        field.name = '_id'
        self.assertEqual(isinstance(field.type, colander.String), True)
        self.assertEqual(field.schema.serialize(), colander.null)
        self.assertEqual(isinstance(field.schema.deserialize(),
                                    bson.objectid.ObjectId), True)
        self.assertRaises(colander.Invalid,
                          field.schema.deserialize,
                          '')
        self.assertRaises(colander.Invalid, field.schema.deserialize, 'No12chars')
        self.assertRaises(colander.Invalid,
                          field.schema.deserialize,
                          'greaterthan12chars')
        field.schema.deserialize('0123456789AB')


class TestDocuments(unittest.TestCase):

    def setUp(self):

        class MainEmbeddedDocument(object):

            from mongobag import EmbeddedDocumentMeta

            __metaclass__ = EmbeddedDocumentMeta

        class MainDocument(object):

            from mongobag import DocumentMeta
            from mongobag import ObjectId

            __metaclass__ = DocumentMeta

            _id = ObjectId()

        self.MainEmbeddedDocument = MainEmbeddedDocument
        self.MainDocument = MainDocument

    def tearDown(self):
        pass

    def test_get_document_registry(self):
        from mongobag import get_document_registry
        registry = get_document_registry(self.MainDocument)
        self.assertIn('_id', registry.fields)
        self.assertEqual('_id', registry.fields['_id'].name)

    def test_get_document_schema(self):
        from mongobag import get_document_registry
        get_document_registry(self.MainDocument)
