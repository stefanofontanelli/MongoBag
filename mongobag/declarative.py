# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .utils import Registry
import colander
import fields
import logging
import mongoq


__all__ = []


log = logging.getLogger(__file__)


class DocumentMetaClass(type):

    _DATABASE = '__database__'
    _COLLECTION = '__collection__'
    _REGISTRY = '__registry__'
    _SCHEMA = '__schema__'
    _VALIDATOR = '__validator__'

    def __new__(cls, name, bases, attrs):

        if '_id' not in attrs:
            attrs['_id'] = fields.ObjectId()

        if cls._DATABASE not in attrs:
            attrs[cls._DATABASE] = None

        if cls._COLLECTION not in attrs:
            attrs[cls._COLLECTION] = name.lower()

        if cls._VALIDATOR not in attrs:
            attrs[cls._VALIDATOR] = None

        if cls._REGISTRY not in attrs:
            attrs[cls._REGISTRY] = Registry(cls, bases, attrs)

        if cls._SCHEMA not in attrs:
            attrs[cls._SCHEMA] = attrs[cls._REGISTRY].schema

        for field in attrs[cls._REGISTRY].fields:
            attrs[field] = getattr(mongoq.Q, field)

        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        # Bind Registry to cls.
        getattr(cls, cls._REGISTRY).class_ = cls

    def __setattr__(cls, name, value):

        if name in getattr(cls, cls._REGISTRY).fields:
            msg = 'Cannot replace document field: %s.' % name
            raise AttributeError(msg)

        if not hasattr(value, 'serialize') or \
           not hasattr(value, 'deserialize'):
            type.__setattr__(cls, name, value)
            return None

        for class_ in [cls] + cls.__all_subclasses__():
            registry = getattr(class_, class_._REGISTRY)
            setattr(registry, name, value)

        # Set mongoq.Query instead of field in the parent class only!
        type.__setattr__(cls, name, getattr(mongoq.Q, name))

    def __all_subclasses__(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                         for g in s.__all_subclasses__()]


class Document(object):

    __metaclass__ = DocumentMetaClass

    def __new__(cls, **kwargs):
        try:
            kwargs = getattr(cls, cls._SCHEMA).deserialize(kwargs)

        except colander.Invalid as e:
            if e.msg and e.msg.startswith('Unrecognized keys in mapping'):
                msg = 'Unrecognized keyword arguments for {}: {}'
                raise TypeError(msg.format(e.node.name,
                                           e.msg.mapping['val'].keys()))
            raise e
        return object.__new__(cls, **kwargs)

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __getattribute__(self, name):

        try:
            _kwargs = object.__getattribute__(self, '_kwargs')

        except AttributeError:
            _kwargs = {}

        try:
            return _kwargs[name]

        except KeyError:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):

        registry = getattr(self, self.__class__._REGISTRY)
        if name in registry.fields:
            value = registry.schema[name].deserialize(value)

        object.__setattr__(self, name, value)

    def __eq__(self, other):

        if self._id is None and other._id is None:
            return self.serialize() == other.serialize()

        return self._id == other._id

    def serialize(self):

        serialized = {}
        for name in getattr(self.__class__, self.__class__._REGISTRY).fields:

            value = getattr(self, name, colander.null)

            if value is colander.null:
                continue

            serialized[name] = value

        return serialized

    def save(self, database=None):

        if database is None:
            database = getattr(self, self.__class__._DATABASE, None)

        if database is None:
            database = getattr(self.__class__, self.__class__._DATABASE, None)

        if database is None:
            raise ValueError('You must specify a database.')

        collection = database[getattr(self.__class__,
                                      self.__class__._COLLECTION)]

        _id = collection.save(self.serialize())
        if self._id is None and not _id is None:
            # Insert has been performed.
            self._id = _id

        elif self._id is None and _id is None:
            msg = 'Error during save: document did not receive any _id.'
            raise RuntimeWarning(msg)

        setattr(self, self.__class__._COLLECTION, collection)

    def delete(self, database=None):

        if database is None:
            database = getattr(self, self.__class__._DATABASE, None)

        if database is None:
            database = getattr(self.__class__, self.__class__._DATABASE, None)

        if database is None:
            raise ValueError('You must specify a database.')

        collection = database[getattr(self.__class__,
                                      self.__class__._COLLECTION)]

        return collection.remove(self._id)
