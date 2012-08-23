# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .fields import ObjectId
from .utils import Registry
import colander
import logging
import mongoq


__all__ = []


log = logging.getLogger(__file__)


class DocumentMetaClass(type):

    _COLLECTION = '__collection__'
    _REGISTRY = '__registry__'
    _VALIDATOR = '__validator__'

    def __new__(cls, name, bases, attrs):

        if '_id' not in attrs:
            attrs['_id'] = ObjectId(missing=colander.null,
                                    default=colander.null)

        if cls._COLLECTION not in attrs:
            attrs[cls._COLLECTION] = name.lower()

        if cls._VALIDATOR not in attrs:
            attrs[cls._VALIDATOR] = None

        if cls._REGISTRY not in attrs:
            attrs[cls._REGISTRY] = None

        def __init__(self, **kwargs):
            try:
                registry = getattr(self, self.__class__._REGISTRY)
                self._values = registry.schema.deserialize(kwargs)

            except colander.Invalid as e:
                if e.msg and e.msg.startswith('Unrecognized keys in mapping'):
                    msg = 'Unrecognized keyword arguments for {}: {}'
                    msg = msg.format(e.node.name or self.__class__.__name__,
                                     e.msg.mapping['val'])
                    raise TypeError(msg)
                raise e

        attrs['__init__'] = __init__

        def __getattribute__(self, name):

            try:
                values = object.__getattribute__(self, '_values')

            except AttributeError:
                values = {}

            registry = object.__getattribute__(self, '__class__')._REGISTRY
            registry = object.__getattribute__(self, registry)
            if name in registry.fields:
                return values.get(name)

            return object.__getattribute__(self, name)

        attrs['__getattribute__'] = __getattribute__

        def __setattr__(self, name, value):

            registry = getattr(self, self.__class__._REGISTRY)
            if name in registry.fields:
                self._values[name] = registry.schema[name].deserialize(value)

            object.__setattr__(self, name, value)

        attrs['__setattr__'] = __setattr__

        def __eq__(self, other):
            return self.asdict() == other.asdict()

        attrs['__eq__'] = __eq__

        def __repr__(self):
            return "<%s %s>" % (self.__class__.__name__, self._values)

        attrs['__repr__'] = __repr__

        def asdict(self):
            registry = getattr(self, self.__class__._REGISTRY)
            return registry.schema.serialize(self._values)

        attrs['asdict'] = asdict

        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        # Bind Registry to cls.
        if getattr(cls, cls._REGISTRY) is None:
            type.__setattr__(cls, cls._REGISTRY, Registry(cls, bases, attrs))

        fields = getattr(cls, cls._REGISTRY).fields
        for name in fields:
            type.__setattr__(cls, name, getattr(mongoq.Q, name))

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


Document = DocumentMetaClass('Document', (object,), {})
