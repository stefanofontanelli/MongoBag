# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import types
import colander
import datetime
import logging


__all__ = []


log = logging.getLogger(__file__)


class Field(colander.SchemaNode):
    """Base class for fields. """

    def serialize(self, appstruct=colander.null):

        if not isinstance(self.default,
                          colander.deferred) and callable(self.default):

            default = self.default()

        else:
            default = self.default

        if appstruct is colander.null:
            appstruct = default

        if isinstance(appstruct, colander.deferred):
            appstruct = colander.null

        # Return deserialized value!
        # RATIONALE: return field value untouched!
        return self.deserialize(appstruct)

    def deserialize(self, cstruct=colander.null):

        appstruct = self.typ.deserialize(self, cstruct)

        if self.preparer is not None:
            appstruct = self.preparer(appstruct)

        if appstruct is colander.null:

            if not isinstance(self.missing,
                              colander.deferred) and callable(self.missing):

                missing = self.missing()

            else:
                missing = self.missing

            appstruct = missing

            if appstruct is colander.required:
                raise colander.Invalid(self, colander._('Required'))

            if isinstance(appstruct, colander.deferred):
                raise colander.Invalid(self, colander._('Required'))

            return appstruct

        if self.validator is not None:
            if not isinstance(self.validator, colander.deferred):
                self.validator(self, appstruct)

        return appstruct

    def clone(self):
        cloned = self.__class__()
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned


class ObjectId(Field):

    def __init__(self, missing=colander.null, **kwargs):
        Field.__init__(self, types.ObjectId(), missing=missing, **kwargs)


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

    def deserialize(self, cstruct=colander.null):

        if isinstance(cstruct, datetime.date):
            return cstruct

        return Field.deserialize(self, cstruct)


class DateTime(Field):

    def __init__(self, tzinfo=colander.iso8601.Utc(), **kwargs):
        Field.__init__(self, colander.DateTime(tzinfo), **kwargs)

    def deserialize(self, cstruct=colander.null):

        if isinstance(cstruct, datetime.datetime):
            return cstruct

        return Field.deserialize(self, cstruct)


class Time(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, colander.Time(), **kwargs)

    def deserialize(self, cstruct=colander.null):

        if isinstance(cstruct, datetime.time):
            return cstruct

        return Field.deserialize(self, cstruct)


class Embedded(Field):

    def __init__(self, typ, **kwargs):
        self.Document = typ
        try:
            self.schema = getattr(typ, typ.__class__._SCHEMA).clone()
            if '_id' in self.schema:
                self.schema.__delitem__('_id')

        except AttributeError:
            raise ValueError('%s is not a document.' % typ.__name__)

        Field.__init__(self, colander.Mapping, *self.schema.children, **kwargs)


class EmbeddedList(Field):

    def __init__(self, typ, **kwargs):
        Field.__init__(self, colander.Sequence(False), Embedded(typ), **kwargs)


# FIXME: add class Reference and list of Reference ?
