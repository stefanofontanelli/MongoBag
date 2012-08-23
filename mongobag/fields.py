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


class Document(Field):

    def __init__(self, class_, *fields, **kwargs):
        self.class_ = class_
        Field.__init__(self,
                       colander.Mapping(unknown='raise'), *fields, **kwargs)

    def serialize(self, appstruct):

        if not isinstance(self.default,
                          colander.deferred) and callable(self.default):

            default = self.default()

        else:
            default = self.default

        if appstruct is colander.null:
            appstruct = default

        if isinstance(appstruct, colander.deferred):
            appstruct = colander.null

        if appstruct is colander.null:
            raise ValueError('Cannot serialize null object.')

        cstruct = self.typ.serialize(self, appstruct)
        return {name: cstruct[name]
                for name in cstruct
                if cstruct[name] != colander.null}

    def deserialize(self, cstruct):
        appstruct = Field.deserialize(self, cstruct)
        return {name: appstruct[name]
                for name in appstruct
                if appstruct[name] != colander.null}

    def clone(self):
        cloned = self.__class__(self.class_)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned


class EmbeddedDocument(Field):

    def __init__(self, class_, **kwargs):

        self.class_ = class_

        try:
            getattr(class_, class_.__class__._REGISTRY)

        except AttributeError:
            raise ValueError('%s is not a document.' % class_.__name__)

        Field.__init__(self, colander.Mapping(unknown='raise'), **kwargs)

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

        if isinstance(appstruct, self.class_):
            # appstruct is an object of self.class_
            appstruct = appstruct.asdict()

        if '_id' in appstruct:
            appstruct.pop('_id')

        return appstruct

    def deserialize(self, cstruct=colander.null):

        if isinstance(cstruct, self.class_):
            return cstruct

        if cstruct is colander.null:

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

        if cstruct is None:
            return cstruct

        # Try deserilization on self.cls and all subclasses!
        results = {}
        error = None
        for class_ in [self.class_] + self.class_.__all_subclasses__():
            registry = getattr(class_, class_.__class__._REGISTRY)
            # Calculate set of common fields between cstruct and class_.
            common = frozenset(set(cstruct.keys()) & registry.fields)
            try:
                results[common] = class_(**cstruct.copy())

            except colander.Invalid as e:
                error = e
                continue

        if not results:
            raise e

        # Return the instance of class with maximum number of common fields.
        scores = {len(set_):set_ for set_ in results.keys()}
        key = max(scores.keys())
        appstruct = results[scores[key]]

        if self.preparer is not None:
            appstruct = self.preparer(appstruct)

        if self.validator is not None:
            if not isinstance(self.validator, colander.deferred):
                self.validator(self, appstruct)

        return appstruct

    def clone(self):
        cloned = self.__class__(self.class_)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned


class EmbeddedList(Field):

    def __init__(self, class_, **kwargs):
        self.class_ = class_
        Field.__init__(self, colander.Sequence(False),
                       EmbeddedDocument(class_), **kwargs)

    def clone(self):
        cloned = self.__class__(self.class_)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned

# FIXME: add class Reference and list of Reference ?
