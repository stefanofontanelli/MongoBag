# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .fields import Field
from .fields import Document


def get_cls_collection(cls):
    return getattr(cls, cls._COLLECTION)


class Registry(object):

    def __init__(self, class_, bases, attrs):

        self.class_ = class_
        self.validator = attrs[class_.__class__._VALIDATOR]
        object.__setattr__(self, 'schema',
                           Document(self.class_, validator=self.validator))
        self.fields = set()

        for base in bases:
            try:
                registry = getattr(base, base._REGISTRY)

            except AttributeError:
                continue

            else:
                for field in registry.fields:
                    field = registry.schema[field].clone()
                    try:
                        self.schema[field.name] = field

                    except KeyError:
                        self.schema.add(field)

                    self.fields.add(field.name)

        for name in attrs:

            field = attrs[name]

            if not isinstance(field, Field):
                continue

            field.name = name
            try:
                self.schema[field.name] = field

            except KeyError:
                self.schema.add(field)

            self.fields.add(field.name)

    def __setattr__(self, name, value):

        if not isinstance(value, Field):
            object.__setattr__(self, name, value)
            return None

        self.fields.add(name)
        value.name = name
        self.schema.add(value)

    def __delattr__(self, name):

        if name not in self.fields:
            object.__delattr__(self, name)

        self.fields.remove(name)
        del self.schema[name]
