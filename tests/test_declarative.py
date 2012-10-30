# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import unittest


log = logging.getLogger(__name__)


class TestDeclarative(unittest.TestCase):

    def test_init(self):

        from .models import (MainDocument,
                             SimpleDocument)
        from mongobag import DocumentTypeError
        from mongobag.declarative import DocumentList

        self.assertRaises(DocumentTypeError, SimpleDocument)
        self.assertRaises(DocumentTypeError,
                          SimpleDocument,
                          name='My Name',
                          surname='No Surname')
        simple_doc = SimpleDocument(name='My Simple Document')
        self.assertRaises(DocumentTypeError, MainDocument)
        self.assertRaises(DocumentTypeError,
                          MainDocument,
                          string='A string',
                          integer=0,
                          boolean=False,
                          float=1.0,
                          ed={})
        doc = MainDocument(string='A string',
                           integer=1,
                           boolean=True,
                           float=2.0,
                           ed=SimpleDocument(name='Simple Document as Embedded Doc'))
        self.assertEqual(isinstance(doc.ed, SimpleDocument), True)
        doc = MainDocument(string='A string',
                           integer=1,
                           boolean=True,
                           float=2.0,
                           edl=[SimpleDocument(name='Simple Document as Embedded Doc')])
        self.assertEqual(isinstance(doc.edl, DocumentList), True)
        self.assertRaises(DocumentTypeError, doc.edl.append, None)
        self.assertRaises(DocumentTypeError, doc.edl.insert, 0, None)
        self.assertRaises(DocumentTypeError, doc.edl.extend, [None])
        self.assertEqual(isinstance(doc.edl[0], SimpleDocument), True)

    def test_setattr(self):
        from .models import EmbeddedDocument, MainDocument, SimpleDocument
        from mongobag import DocumentAttributeError
        simple_doc = SimpleDocument(name='My Simple Document')
        self.assertRaises(DocumentAttributeError, setattr, simple_doc, 'myattr', None)
        doc = MainDocument(string='A string', integer=1, boolean=True, float=2.0)
        doc.ed = simple_doc
        self.assertEqual(doc.ed, simple_doc)
        doc.ed = None
        self.assertEqual(doc.ed, None)
        self.assertRaises(DocumentAttributeError, setattr, doc, 'edl', None)
        self.assertRaises(DocumentAttributeError, setattr, doc, 'edl', [simple_doc, None])

    def test_deserialize(self):
        from .models import MainDocument
        from .models import SimpleDocument
        from mongobag import DocumentTypeError
        params = dict(name='My Simple Document')
        doc = SimpleDocument.deserialize(**params)
        self.assertTrue(isinstance(doc, SimpleDocument))
        params = dict(string='A string', integer=1, boolean=True, float=2.0, ed=None, edl=None)
        doc = MainDocument.deserialize(**params)
        self.assertTrue(isinstance(doc, MainDocument))
        params = dict(string='A string', integer=1, boolean=True, float=2.0, 
                      ed=dict(name='My Simple Document'), edl=None)
        doc = MainDocument.deserialize(**params)
        self.assertTrue(isinstance(doc, MainDocument))
        params = dict(string='A string', integer=1, boolean=True, float=2.0, 
                      ed=dict(name='My Simple Document'), edl=[])
        doc = MainDocument.deserialize(**params)
        self.assertTrue(isinstance(doc, MainDocument))
        params = dict(string='A string', integer=1, boolean=True, float=2.0, 
                      ed=dict(name='My Simple Document', surname='Surname'), edl=[])
        self.assertRaises(DocumentTypeError,  MainDocument.deserialize, **params)

    def test_serialize(self):
        from .models import MainDocument
        from .models import SimpleDocument
        doc = MainDocument(string='A string',
                           integer=1,
                           boolean=True,
                           float=2.0,
                           ed=SimpleDocument(name='Embedded Document'),
                           edl=[SimpleDocument(name='Simple Document as Embedded Doc')])
        values = doc.serialize()
        for name in ['string', 'ed', 'float', 'edl', 'datetime', 'boolean', 'time', 'date', 'integer', '_id']:
            self.assertIn(name, values)

        self.assertIn('name', values['ed'])
        self.assertIn('name', values['edl'][0])

    def test_no_abstract_document_id_presence(self):
        from mongobag import DocumentMeta
        self.assertRaises(TypeError, DocumentMeta, 'MyDoc', (object,), {})

    def test_meta_setattr(self):
        from .models import SimpleDocument
        from mongobag import DocumentMeta, EmbeddedDocument, EmbeddedList, ObjectId
        class_ = DocumentMeta('MyDoc', (object,), {'_id': ObjectId()})
        class_.embedded_doc = EmbeddedDocument(SimpleDocument)
        class_.embedded_list = EmbeddedList(SimpleDocument)
        class_.my_attr = None
        self.assertEqual(class_.my_attr, None)
        self.assertRaises(AttributeError, setattr, class_, '_id', None)
