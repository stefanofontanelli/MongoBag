# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import types
import colander
import logging

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

    def __init__(self, default_tzinfo=None, *children, **kwargs):
        super(DateTime, self).__init__(colander.DateTime(default_tzinfo),
                                       *children,
                                       **kwargs)


class Date(Field):

    def __init__(self, *children, **kwargs):
        super(Date, self).__init__(colander.Date(),
                                   *children,
                                   **kwargs)


class Time(Field):

    def __init__(self, *children, **kwargs):
        super(Time, self).__init__(colander.Time(),
                                   *children,
                                   **kwargs)


class GlobalObject(Field):

    def __init__(self, package, *children, **kwargs):
        super(GlobalObject, self).__init__(colander.GlobalObject(package),
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
        self._schema = colander.SchemaNode(colander.Mapping(unknown='raise'))

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
                pass
            else:
                self.embedded[name] = attr

            #if isinstance(attr, None):
            #    self.refs[name] = attr

    @property
    def schema(self):
        return self._schema


_DATABASE = '__database__'
_COLLECTION = '__collection__'
_REGISTRY = '__registry__'
_SCHEMA = '__schema__'
_VALIDATE = '__validate__'


class EmbeddedDocumentMeta(type):

    def __new__(cls, name, bases, attrs):

        if _DATABASE not in attrs:
            attrs[_DATABASE] = None

        if _COLLECTION not in attrs:
            attrs[_COLLECTION] = name.lower()

        if _REGISTRY not in attrs:
            attrs[_REGISTRY] = Registry(cls, name, bases, attrs)

        if _SCHEMA not in attrs:
            attrs[_SCHEMA] = attrs[_REGISTRY].schema

        if _VALIDATE not in attrs:
            attrs[_VALIDATE] = True

        for name, field in attrs.items():

            """
            def getter(self):
                value = self.get(name)
                if not value is None and isinstance(field.type, Document):
                    value = field.type(**value)
                return value

            def setter(self, value):

                if not value is None and isinstance(field.type, Document):
                    value = field.type(**value)
                else:
                    value = field.type(value)

                self[name] = value

            def deleter(self, value):
                self.pop(name, None)

            getter.__name__ = '__get_{}__'.format(name)
            setter.__name__ = '__set_{}__'.format(name)
            deleter.__name__ = '__del_{}__'.format(name)
            attrs['__fields__'][name] = field
            attrs[name] = property(getter, setter, deleter)
            """

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
