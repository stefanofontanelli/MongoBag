# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .types import ObjectId as objectid
import colander
import datetime
import logging


__all__ = []


log = logging.getLogger(__file__)


unassigned = colander.null


class Field(colander.SchemaNode):
    """Base class for all mongobag fields. """
    
    def clone(self):
        cloned = self.__class__()
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned


class ObjectId(Field):

    def __init__(self, missing=colander.null, **kwargs):
        Field.__init__(self, objectid(), missing=missing, **kwargs)


class Integer(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Integer(), **kwargs)


class String(Field):

    def __init__(self, encoding=None, **kwargs):
        Field.__init__(self, colander.String(encoding), **kwargs)


class Boolean(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Boolean(), **kwargs)


class Float(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Float(), **kwargs)


class Date(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Date(), **kwargs)


class DateTime(Field):

    def __init__(self, tzinfo=colander.iso8601.Utc(), **kwargs):
        Field.__init__(self, colander.DateTime(tzinfo), **kwargs)


class Time(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Time(), **kwargs)


class EmbeddedDocument(Field):

    def __init__(self, class_, **kwargs):

        self.class_ = class_

        try:
            schema = getattr(class_, class_._SCHEMA)

        except AttributeError:
            raise ValueError('%s is not a document.' % class_)

        Field.__init__(self,
                       schema.typ,
                       *schema.children,
                       **kwargs)

    def clone(self):
        cloned = self.__class__(self.class_)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned


class EmbeddedList(Field):

    def __init__(self, class_, **kwargs):
        self.class_ = class_
        Field.__init__(self,
                       colander.Sequence(False),
                       EmbeddedDocument(class_),
                       **kwargs)

    def clone(self):
        cloned = self.__class__(self.class_)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned

# FIXME: add class Reference and list of Reference ?
