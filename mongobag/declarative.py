# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .exc import (DocumentAttributeError,
                  NoResultFound,
                  DocumentTypeError)
from .schemas import (Field,
                      EmbeddedDocument,
                      EmbeddedList,
                      ObjectId)
import colander
import logging
import mongoq
import warnings


__all__ = ['DocumentMeta', 'Document']


log = logging.getLogger(__file__)


class DocumentMeta(type):

    def __new__(cls, name, bases, attrs):

        # The "constant" below are used by mongobag to store information.
        _ABSTRACT = '__abstract__'  # identify no persistent document class.
        _COLLECTION = '__collection__'  # collection name/object of the document.
        _SCHEMA = '__schema__'  # Colander schema object.

        if _ABSTRACT not in attrs:
            attrs[_ABSTRACT] = False

        if len([base
                for base in bases
                if isinstance(base, cls) and \
                   getattr(base, _COLLECTION, None)]) > 1:
            msg = 'Multiple base classes of {} define {}.'
            warnings.warn(msg.format(name, _COLLECTION), SyntaxWarning)

        class_ = type.__new__(cls, name, bases, attrs)
        type.__setattr__(class_, '_ABSTRACT', _ABSTRACT)
        type.__setattr__(class_, '_COLLECTION', _COLLECTION)
        type.__setattr__(class_, '_SCHEMA', _SCHEMA)

        return class_

    def __init__(cls, name, bases, attrs):
        # NOTE: cls is the document class instance NOT the metaclass!
        type.__init__(cls, name, bases, attrs)

        abstract = getattr(cls, cls._ABSTRACT)

        if not abstract and getattr(cls, cls._COLLECTION, None) is None:
            # Add a default name for documents collection.
            # MongoBag use this name to load the pymongo collection obj.
            type.__setattr__(cls, cls._COLLECTION, cls.__name__.lower())

        if not abstract and getattr(cls, '_id', None) is None:
            raise TypeError('Not abstract classes must have an _id field.')

        # Create a colander schema of the document.
        schema = colander.SchemaNode(colander.Mapping(unknown='raise'))
        type.__setattr__(cls, cls._SCHEMA, schema)
        type.__setattr__(cls, '__attrs__', {})
        type.__setattr__(cls, '__fields__', {})
        type.__setattr__(cls, '__embedded_docs__', {})
        type.__setattr__(cls, '__embedded_lists__', {})

        for base in bases:
            try:
                base_attrs = base.__attrs__
                base_fields = base.__fields__
                base_embedded_docs = base.__embedded_docs__
                base_embedded_lists = base.__embedded_lists__

            except AttributeError:
                continue

            else:
                for name in base_attrs:
                    attr = base_attrs[name].clone()
                    cls.__attrs__[attr.name] = attr

                    if attr.name in base_fields:
                        cls.__fields__[attr.name] = attr

                    if attr.name in base_embedded_docs:
                        cls.__embedded_docs__[attr.name] = attr

                    if attr.name in base_embedded_lists:
                        cls.__embedded_lists__[attr.name] = attr

        for name in attrs:

            attr = attrs[name]

            if not isinstance(attr, Field):
                continue

            attr.name = name
            cls.__attrs__[name] = attr

            if isinstance(attr, EmbeddedDocument):
                cls.__embedded_docs__[name] = attr

            elif isinstance(attr, EmbeddedList):
                cls.__embedded_lists__[name] = attr

            else:
                cls.__fields__[name] = attr

        schema = getattr(cls, cls._SCHEMA)
        for name in cls.__attrs__:
            schema.add(cls.__attrs__[name])

        # Replace fields with MongoQ objects:
        # user can perform query using the style MyClass.attr == value
        # instead of Mongo syntax.
        for name in cls.__attrs__:
            type.__setattr__(cls, name, getattr(mongoq.Q, name))

    def __setattr__(cls, name, value):

        if not isinstance(value, Field) and name in cls.__attrs__:
            raise AttributeError('Attribute value must be a Field instance.')

        elif not isinstance(value, Field):
            return type.__setattr__(cls, name, value)

        value.name = name

        for class_ in [cls] + cls.__all_subclasses__():

            if class_ != cls:
                value = value.clone()

            class_.__attrs__[name] = value

            if isinstance(value, EmbeddedDocument):
                class_.__embedded_docs__[name] = value

            elif isinstance(value, EmbeddedList):
                class_.__embedded_lists__[name] = value

            else:
                class_.__fields__[name] = value                

            schema = getattr(class_, class_._SCHEMA)
            schema.add(value)

        # Set mongoq.Query instead of field in the parent class only!
        type.__setattr__(class_, name, getattr(mongoq.Q, name))

    def __all_subclasses__(cls):
        subclasses = cls.__subclasses__()
        return subclasses + [g for s in subclasses
                               for g in s.__all_subclasses__()]


class Document(object, metaclass=DocumentMeta):

    __abstract__ = True
    _id = ObjectId(missing=colander.null, default=colander.null)

    def __init__(self, **kwargs):

        for name in self.__attrs__:
            value = kwargs.pop(name, colander.null)
            try:
                setattr(self, name, value)

            except DocumentAttributeError as e:
                raise DocumentTypeError(str(e))

        if kwargs:
            msg = 'Unknown arguments: {}'.format(kwargs)
            raise DocumentTypeError(msg)

    def __setattr__(self, name, value):

        if name not in self.__attrs__:
            msg = '{}.{} is not defined'.format(self.__class__.__name__, name)
            raise DocumentAttributeError(msg)

        elif name in self.__fields__:
            value = self.validate_field(name, value)

        elif name in self.__embedded_docs__:
            value = self.validate_embedded_doc(name, value)

        elif name in self.__embedded_lists__:
            value = self.validate_embedded_list(name, value)

        object.__setattr__(self, name, value)

    def validate_field(self, name, value):

        cstruct = str(value) if value != colander.null else value

        try:
            value = getattr(self, self._SCHEMA)[name].deserialize(cstruct)

        except colander.Invalid as e:
            raise DocumentAttributeError(str(e))

        else:
            return value if value != colander.null else None

    def validate_embedded_doc(self, name, value):
        
        schema = self.__embedded_docs__[name]

        if isinstance(value, schema.class_):
            return value

        if value is None:
            value = colander.null

        if value is colander.null:
            try:
                value = schema.deserialize(value)

            except colander.Invalid as e:
                raise DocumentAttributeError(str(e))

            else:
                return value if value != colander.null else None

        msg = 'Cannot set {}.{} to {}: invalid value.'
        msg = msg.format(self.__class__.__name__,
                         name,
                         value,
                         schema.class_)
        raise DocumentAttributeError(msg)

    def validate_embedded_list(self, name, value):

        if isinstance(value, DocumentList):
            return value

        schema = self.__embedded_lists__[name]
        if value is colander.null:
            try:
                value = schema.deserialize(value)

            except colander.Invalid as e:
                raise DocumentAttributeError(str(e))

            else:
                default = DocumentList(schema.class_, [])
                return value if value != colander.null else default

        if not isinstance(value, list):
            msg = 'Cannot set {}.{} to {}: it is not a list.'
            msg = msg.format(self.__class__.__name__, name, value)
            raise DocumentAttributeError(msg)

        try:
            value = DocumentList(schema.class_, value)

        except DocumentTypeError:
            msg = 'Cannot set {}.{} to {}: objects must be {} instances or dicts.'
            msg = msg.format(self.__class__.__name__,
                             name,
                             value,
                             schema.class_.__name__)
            raise DocumentAttributeError(msg)

        return value

    @classmethod
    def deserialize(cls, **kwargs):

        for name in cls.__embedded_docs__:
            schema = cls.__embedded_docs__[name]
            params = kwargs.pop(name, colander.null)
            if params is colander.null or params is None:
                continue
            
            kwargs[name] = schema.class_.deserialize(**params)

        for name in cls.__embedded_lists__:
            schema = cls.__embedded_lists__[name]
            values = kwargs.pop(name, colander.null)
            if values is colander.null or values is None:
                continue
            
            kwargs[name] = DocumentList(schema.class_,
                                        [schema.class_.deserialize(**params)
                                         for params in values])

        candidates = []
        for class_ in [cls] + cls.__all_subclasses__():
            try:
                candidates.append(class_(**kwargs))

            except DocumentTypeError:
                continue

        if len(candidates) > 1:
            msg = 'Cannot deserialize {} using {}: too many candidates.'
            msg = msg.format(cls.__name__, kwargs)
            raise DocumentTypeError(msg)

        if not candidates:
            msg = 'Cannot deserialize {} using {}: no candidates.'
            msg = msg.format(cls.__name__, kwargs)
            raise DocumentTypeError(msg)

        return candidates[0]

    @classmethod
    def find_one(cls, db, criterion, *args, **kwargs):
        doc = db[cls._COLLECTION].find_one(criterion, *args, **kwargs)
        if doc is None:
            msg = 'No result for: {}'.format(criterion)
            raise NoResultFound(msg)

        return cls.deserialize(**doc) if doc else None

    @classmethod
    def find(cls, db, criterion, **kwargs):
        for doc in db[cls._COLLECTION].find(criterion, **kwargs):
            yield cls.deserialize(**doc)

    def serialize(self):
        """ Convert document to dict.
        """
        values = {name: getattr(self, name)
                  for name in self.__fields__
                  if getattr(self, name, colander.null) != colander.null}
        values.update({name: getattr(self, name).serialize()
                       for name in self.__embedded_docs__
                       if getattr(self, name, colander.null) != colander.null})
        values.update({name: [obj.serialize()
                              for obj in getattr(self, name)]
                       for name in self.__embedded_lists__
                       if getattr(self, name, colander.null) != colander.null})
        return values

    def save(self, db, **kwargs):
        id_ = db[cls._COLLECTION].save(self.serialize(), **kwargs)
        if not id_ is None:
            self._id = id_

        return id_

    def insert(self, db, **kwargs):
        self._id = db[cls._COLLECTION].insert(self.serialize(), **kwargs)
        return self._id

    def update(self, db, **kwargs):
        return db[cls._COLLECTION].update(self.serialize(), **kwargs)

    def remove(self, db, **kwargs):
        return db[cls._COLLECTION].remove(self.serialize(), **kwargs)


class DocumentList(list):

    def __init__(self, class_, list_):
        self.class_ = class_
        list.__init__(self, [self.validate_document(doc)
                             for doc in list_])

    def append(self, obj):
        list.append(self, self.validate_document(obj))

    def extend(self, list_):
        list.extend(self, [self.validate_document(doc)
                           for doc in list_])

    def insert(self, i, obj):
        list.insert(self, i, self.validate_document(obj))

    def validate_document(self, doc):

        if not isinstance(doc, self.class_):
            msg = 'Object {} must be an instance of {}.'
            raise DocumentTypeError(msg.format(doc, self.class_.__name__))

        return doc