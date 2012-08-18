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


class EmbeddedDocument(colander.Mapping):

    def __init__(self, typ):
        colander.Mapping.__init__(self, 'raise')
        self.typ = typ
        try:
            self.schema = getattr(typ, typ.__class__._SCHEMA).clone()
            if '_id' in self.schema:
                self.schema.__delitem__('_id')

        except AttributeError:
            raise ValueError('%s is not a document.' % typ.__name__)

    def serialize(self, node, obj):
        """ Convert obj to a dict.
        """

        if obj is colander.null:
            return {}

        if not isinstance(obj, self.typ):
            msg = '{} is not an {} object.'.format(obj, self.typ.__name__)
            raise colander.Invalid(node, msg)

        return obj.serialize()

    def deserialize(self, node, kwargs):
        """ Convert a dict to an object.
        """

        if kwargs is colander.null:
            return self.typ()

        if isinstance(kwargs, self.typ):
            return kwargs

        try:
            obj = self.typ(**kwargs)

        except colander.Invalid:
            msg = 'Wrong params for {} object'.format(self.typ.__name__)
            raise colander.Invalid(node, msg)

        return obj
