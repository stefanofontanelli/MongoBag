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


class Field(object):

    def __init__(self, type_, *children, **kwargs):

        if isinstance(type_, colander.SchemaType):
            self._schema = colander.SchemaNode(type_, *children, **kwargs)
        else:
            raise ValueError("Type of argument 'type_' is not supported.")

    @property
    def type(self):
        return self._schema.typ

    @property
    def name(self):
        return self._schema.name

    @name.setter
    def name(self, name):
        self._schema.name = name

    @property
    def schema(self):
        return self._schema


class String(Field):

    def __init__(self, encoding=None, *children, **kwargs):
        super(String, self).__init__(colander.String(encoding),
                                     *children,
                                     **kwargs)


class Integer(Field):

    def __init__(self, *children, **kwargs):
        super(Integer, self).__init__(colander.Int(),
                                      *children,
                                      **kwargs)


class Boolean(Field):

    def __init__(self, *children, **kwargs):
        super(Boolean, self).__init__(colander.Boolean(),
                                      *children,
                                      **kwargs)


class Float(Field):

    def __init__(self, *children, **kwargs):
        super(Float, self).__init__(colander.Float(),
                                    *children,
                                    **kwargs)


class Decimal(Field):

    def __init__(self, *children, **kwargs):
        super(Decimal, self).__init__(colander.Decimal(),
                                      *children,
                                      **kwargs)


class DateTime(Field):

    def __init__(self, tzinfo=colander.iso8601.Utc(), *children, **kwargs):
        super(DateTime, self).__init__(types.DateTime(tzinfo),
                                       *children,
                                       **kwargs)


class Date(Field):

    def __init__(self, *children, **kwargs):
        super(Date, self).__init__(types.Date(),
                                   *children,
                                   **kwargs)


class Time(Field):

    def __init__(self, *children, **kwargs):
        super(Time, self).__init__(types.Time(),
                                   *children,
                                   **kwargs)


class GlobalObject(Field):

    def __init__(self, package, *children, **kwargs):
        super(GlobalObject, self).__init__(types.GlobalObject(package),
                                           *children,
                                           **kwargs)


class Mapping(Field):

    def __init__(self, type_, unknown='ignore', **kwargs):

        try:
            registry = get_document_registry(type_)
        except AttributeError:
            raise ValueError('type_ must be a document.')

        super(Mapping, self).__init__(colander.Mapping(unknown),
                                      *registry.schema.children,
                                      **kwargs)


class Tuple(Field):

    def __init__(self, type_, **kwargs):

        try:
            registry = get_document_registry(type_)
        except AttributeError:
            raise ValueError('type_ must be a document.')

        super(Tuple, self).__init__(colander.Tuple(),
                                    *(registry.schema,),
                                    **kwargs)


class Sequence(Field):

    def __init__(self, type_, accept_scalar=False, **kwargs):

        try:
            registry = get_document_registry(type_)
        except AttributeError:
            raise ValueError('type_ must be a document.')

        super(Sequence, self).__init__(colander.Sequence(accept_scalar),
                                       *(registry.schema,),
                                       **kwargs)


class ObjectId(Field):

    def __init__(self, encoding=None, *children, **kwargs):
        super(ObjectId, self).__init__(types.ObjectId(),
                                       default=colander.null,
                                       missing=colander.null,
                                       *children,
                                       **kwargs)


class Registry(object):

    def __init__(self, class_, name, bases, attrs):

        self.class_ = class_
        self.name = name
        self.bases = bases
        self.attrs = attrs
        self.fields = {}
        self.refs = {}
        self.embedded = {}
        validator = attrs.get(_VALIDATOR, None)
        self._schema = colander.SchemaNode(colander.Mapping(unknown='raise'),
                                                            validator=validator)

        for name, attr in self.attrs.items():

            if not isinstance(attr, Field):
                continue

            if not attr.name:
                attr.name = name

            self.fields[name] = attr
            self._schema.add(attr.schema)

            try:
                get_document_registry(attr.type)
            except AttributeError:
                continue
            else:
                self.embedded[name] = attr

    @property
    def schema(self):
        return self._schema


_DATABASE = '__database__'
_COLLECTION = '__collection__'
_REGISTRY = '__registry__'
_SCHEMA = '__schema__'
_VALIDATION = '__validation__'
_VALIDATOR = '__validator__'


class EmbeddedDocumentMeta(type):

    def __new__(cls, name, bases, attrs):

        if _DATABASE not in attrs:
            attrs[_DATABASE] = None

        if _COLLECTION not in attrs:
            attrs[_COLLECTION] = name.lower()

        if _VALIDATOR not in attrs:
            attrs[_VALIDATOR] = None

        if _REGISTRY not in attrs:
            attrs[_REGISTRY] = Registry(cls, name, bases, attrs)

        if _SCHEMA not in attrs:
            attrs[_SCHEMA] = attrs[_REGISTRY].schema

        if _VALIDATION not in attrs:
            attrs[_VALIDATION] = True

        for name in attrs[_REGISTRY].fields:
            attrs[name] = getattr(mongoq.Q, name)

        def __init__(self, **kwargs):

            if getattr(self, _VALIDATION):
                kwargs = getattr(self, _SCHEMA).deserialize(kwargs)

            for name in kwargs:
                setattr(self, name, kwargs[name])

        attrs['__init__'] = __init__

        def __setattr__(self, name, value):

            fields = getattr(self, _REGISTRY).fields

            if name not in fields:
                return object.__setattr__(self, name, value)

            field = fields[name]

            if getattr(self, _VALIDATION):
                value = field.schema.deserialize(value)

            if isinstance(field, Mapping):
                value = field.type(**value)

            elif isinstance(field, Tuple):
                value = tuple([field.type(**kwargs) for kwargs in value])

            elif isinstance(field, Sequence):
                value = [field.type(**kwargs) for kwargs in value]

            object.__setattr__(self, name, value)

        attrs['__setattr__'] = __setattr__

        return super(EmbeddedDocumentMeta, cls).__new__(cls,
                                                        name,
                                                        bases,
                                                        attrs)


class DocumentMeta(EmbeddedDocumentMeta):

    def __new__(cls, name, bases, attrs):

        if '_id' not in attrs:
            raise TypeError("Class '%s' has no '_id' field." % name)

        return super(DocumentMeta, cls).__new__(cls, name, bases, attrs)


def get_document_registry(doc):
    return getattr(doc, _REGISTRY)


def get_document_schema(doc):
    return getattr(doc, _SCHEMA)
