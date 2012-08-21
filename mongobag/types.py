# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import bson
import colander
import datetime
import logging

__all__ = []

log = logging.getLogger(__file__)


class ObjectId(object):

    def serialize(self, node, value):
        """ Return an ObjectId as is.
        """

        if value is colander.null:
            return colander.null

        if not isinstance(value, bson.objectid.ObjectId):
            raise colander.Invalid(node, '%s is not an ObjectId' % value)

        return value

    def deserialize(self, node, value):

        if value is colander.null or isinstance(value, bson.objectid.ObjectId):
            return value

        try:
            value = bson.objectid.ObjectId(value)

        except (TypeError, bson.errors.InvalidId):
            raise colander.Invalid(node, '%s is not a valid ObjectId' % value)

        else:
            return value
