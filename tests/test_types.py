# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import unittest


log = logging.getLogger(__name__)


class TestTypes(unittest.TestCase):

    def test_object_id(self):

        from mongobag import ObjectId
        import bson
        import colander

        field = ObjectId()
        field.name = '_id'
        self.assertEqual(field.serialize(), colander.null)
        self.assertEqual(field.deserialize(), colander.null)

        objectid = bson.objectid.ObjectId('5032a91988382a103b763758')
        self.assertEqual(field.serialize(objectid), str(objectid))
        self.assertEqual(field.deserialize(objectid), objectid)
        self.assertRaises(colander.Invalid, field.serialize, '')
        self.assertRaises(colander.Invalid, field.serialize, {'_id': objectid})
        self.assertRaises(colander.Invalid, field.deserialize, '')
        self.assertRaises(colander.Invalid, field.deserialize, {'_id': objectid})

        for i in range(0, 12):
            self.assertRaises(colander.Invalid, field.deserialize, 'x' * i)
        for i in range(13, 32):
            self.assertRaises(colander.Invalid, field.deserialize, 'x' * i)

        self.assertEqual(str(field.deserialize('5032a91988382a103b763758')), str(objectid))
