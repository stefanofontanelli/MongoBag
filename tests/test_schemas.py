# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import logging
import unittest


log = logging.getLogger(__name__)


class TestSchemas(unittest.TestCase):

    def test_embedded_document(self):

        from mongobag import EmbeddedDocument
        self.assertRaises(ValueError, EmbeddedDocument, None)
