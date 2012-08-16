# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import types
import colander
import logging
import mongoq


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

        return  self.typ.serialize(self, appstruct)

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


class ObjectId(Field):

    def __init__(self, missing=colander.null, **kwargs):
        Field.__init__(self, types.ObjectId(), missing=missing, **kwargs)


class Integer(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, types.Integer(), **kwargs)


class String(Field):

    def __init__(self, encoding=None, **kwargs):
        Field.__init__(self, colander.String(encoding), **kwargs)


class Boolean(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, types.Boolean(), **kwargs)


class Float(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, types.Float(), **kwargs)


class DateTime(Field):

    def __init__(self, tzinfo=colander.iso8601.Utc(), **kwargs):
        Field.__init__(self, types.DateTime(tzinfo), **kwargs)


class Date(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, types.Date(), **kwargs)


class Time(Field):

    def __init__(self, **kwargs):
        Field.__init__(self, types.Time(), **kwargs)


class Embedded(Field):

    def __init__(self, typ, **kwargs):
        Field.__init__(self, types.EmbeddedDocument(typ), **kwargs)


class EmbeddedList(Field):

    def __init__(self, typ, **kwargs):
        Field.__init__(self, colander.Sequence(False), Embedded(typ), **kwargs)


# FIXME: add class Reference and list of Reference ?


class Registry(object):

    def __init__(self, class_, name, bases, attrs):

        self.class_ = class_
        self.name = name
        self.bases = bases
        self.attrs = attrs
        self.validator = attrs[class_._VALIDATOR]
        typ = colander.Mapping(unknown='raise')
        self.schema = colander.SchemaNode(typ, name=name,
                                          validator=self.validator)

        self.fields = {}
        for base in bases:
            try:
                registry = getattr(base, class_._REGISTRY)

            except AttributeError:
                continue

            else:
                self.fields.update(registry.fields)

        for name, field in self.attrs.items():

            if not isinstance(field, Field):
                continue

            field.name = name
            self.fields[name] = field
            self.schema.add(field)


class DocumentMetaclass(type):

    _DATABASE = '__database__'
    _COLLECTION = '__collection__'
    _REGISTRY = '__registry__'
    _SCHEMA = '__schema__'
    _VALIDATOR = '__validator__'

    def __new__(cls, name, bases, attrs):

        if '_id' not in attrs:
            attrs['_id'] = ObjectId()

        if cls._DATABASE not in attrs:
            attrs[cls._DATABASE] = None

        if cls._COLLECTION not in attrs:
            attrs[cls._COLLECTION] = name.lower()

        if cls._VALIDATOR not in attrs:
            attrs[cls._VALIDATOR] = None

        if cls._REGISTRY not in attrs:
            attrs[cls._REGISTRY] = Registry(cls, name, bases, attrs)

        if cls._SCHEMA not in attrs:
            attrs[cls._SCHEMA] = attrs[cls._REGISTRY].schema

        for name in attrs[cls._REGISTRY].fields:
            attrs[name] = getattr(mongoq.Q, name)

        return type.__new__(cls, name, bases, attrs)

    def __setattr__(cls, name, value):

        if name in getattr(cls, cls._REGISTRY).fields:
            raise AttributeError('Cannot replace document fields.')

        type.__setattr__(cls, name, value)


class Document(object):

    __metaclass__ = DocumentMetaclass

    def __init__(self, **kwargs):

        try:
            kwargs = getattr(self, self.__class__._SCHEMA).deserialize(kwargs)

        except colander.Invalid as e:
            if e.msg and e.msg.startswith('Unrecognized keys in mapping'):
                msg = 'Unrecognized keyword arguments for {}: {}'
                raise TypeError(msg.format(e.node.name,
                                           e.msg.mapping['val'].keys()))
            raise e

        for name in kwargs:
            object.__setattr__(self, name, kwargs[name])

    def __setattr__(self, name, value):

        fields = getattr(self, self.__class__._REGISTRY).fields
        if name in fields:
            value = fields[name].deserialize(value)

        object.__setattr__(self, name, value)

    def serialize(self):

        serialized = {}
        for name in getattr(self.__class__, self.__class__._REGISTRY).fields:

            value = getattr(self, name, colander.null)

            if value is colander.null:
                continue

            serialized[name] = value

        return serialized


def get_document_registry(doc):
    return getattr(doc, doc.__class__._REGISTRY)


def get_document_schema(doc):
    return getattr(doc, doc.__class__._SCHEMA)
