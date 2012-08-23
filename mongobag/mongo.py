# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .declarative import Document
from .exc import NoResultFound
from .utils import document_factory
from .utils import get_cls_collection
from pymongo.collection import Collection as PyMongoCollection
import pymongo
import pymongo.errors


class Connection(pymongo.connection.Connection):

    def __getattr__(self, name):
        return Database(self, name)


class Database(pymongo.database.Database):

    def __getattr__(self, name):
        return Collection(self, name)

    def create_collection(self, name, **kwargs):
        opts = {"create": True}
        opts.update(kwargs)
        if name in self.collection_names():
            msg = 'collection %s already exists' % name
            raise pymongo.errors.CollectionInvalid(msg)

        return Collection(self, name, **opts)


class Collection(PyMongoCollection):

    def __init__(self, database, name, create=False, **kwargs):

        PyMongoCollection.__init__(self, database, name, create, **kwargs)

        self._documentClass = None
        for class_ in Document.__all_subclasses__():

            if get_cls_collection(class_) != name:
                continue

            self._documentClass = class_

    def __getattr__(self, name):
        return Collection(self.__database, '%s.%s' % (self.__name, name))

    def save(self, to_save, manipulate=True, safe=False, **kwargs):

        if not isinstance(to_save, Document):
            raise TypeError("cannot save object of type %s" % type(to_save))

        if to_save._id is None:
            id_ = self.insert(to_save, manipulate, safe, **kwargs)
            if not id_ is None:
                to_save._id = id_
        else:
            self.update({'_id': to_save._id}, to_save, True,
                        manipulate, safe, _check_keys=True, **kwargs)

        return to_save._id

    def insert(self, doc_or_docs, manipulate=True,
               safe=False, check_keys=True, continue_on_error=False, **kwargs):

        try:
            for doc in doc_or_docs:
                break

        except TypeError:
            doc_or_docs = [doc_or_docs]

        try:
            docs = [doc.asdict() for doc in doc_or_docs]

        except AttributeError:
            raise TypeError("Wrong document: cannot find asdict method.")

        ids = PyMongoCollection.insert(self, docs, manipulate, safe, check_keys,
                                       continue_on_error, **kwargs)

        for i, doc in enumerate(doc_or_docs):

            id_ = ids[i]
            if id_ is None:
                continue

            doc._id = id_

        return len(docs) == 1 and ids[0] or ids

    def update(self, spec, document, upsert=False, manipulate=False,
               safe=False, multi=False, _check_keys=False, **kwargs):

        if not isinstance(document, Document):
            raise TypeError("cannot save object of type %s" % type(document))

        return PyMongoCollection.update(self, spec, document.asdict(),
                                        upsert, manipulate, safe, multi,
                                        _check_keys, **kwargs)

    def remove(self, spec_or_id=None, safe=False, **kwargs):

        if isinstance(spec_or_id, Document):
            spec_or_id = spec_or_id.asdict()

        return PyMongoCollection.remove(self, spec_or_id, safe, **kwargs)

    def find_one(self, spec_or_id=None, *args, **kwargs):

        if isinstance(spec_or_id, Document):
            spec_or_id = spec_or_id.asdict()

        doc = PyMongoCollection.find_one(self, spec_or_id, *args, **kwargs)

        if doc is None:
            raise NoResultFound('No result for: %s' % spec_or_id)

        if isinstance(doc, Document) or \
           self._documentClass is None:
            return doc

        return document_factory(self._documentClass, **doc)

    def find(self, spec=None, *args, **kwargs):

        if isinstance(spec, Document):
            spec = spec.asdict()

        if not 'slave_okay' in kwargs:
            kwargs['slave_okay'] = self.slave_okay

        if not 'read_preference' in kwargs:
            kwargs['read_preference'] = self.read_preference

        return Cursor(self, spec, *args, **kwargs)


class Cursor(pymongo.cursor.Cursor):

    def __init__(self, collection, spec=None, fields=None, skip=0, limit=0,
                 timeout=True, snapshot=False, tailable=False, sort=None,
                 max_scan=None, as_class=None, slave_okay=False,
                 await_data=False, partial=False, manipulate=True,
                 read_preference=None,
                 _must_use_master=False, _uuid_subtype=None, **kwargs):

        pymongo.cursor.Cursor.__init__(self, collection, spec, fields, skip,
                                       limit, timeout, snapshot, tailable,
                                       sort, max_scan, as_class, slave_okay,
                                       await_data, partial, manipulate,
                                       read_preference, _must_use_master,
                                       _uuid_subtype, **kwargs)

        self._documentClass = collection._documentClass

    def clone(self):
        copy = Cursor(self.__collection, self.__spec, self.__fields,
                      self.__skip, self.__limit, self.__timeout,
                      self.__snapshot, self.__tailable)
        copy.__ordering = self.__ordering
        copy.__explain = self.__explain
        copy.__hint = self.__hint
        copy.__batch_size = self.__batch_size
        copy.__max_scan = self.__max_scan
        copy.__as_class = self.__as_class
        copy.__slave_okay = self.__slave_okay
        copy.__await_data = self.__await_data
        copy.__partial = self.__partial
        copy.__manipulate = self.__manipulate
        copy.__read_preference = self.__read_preference
        copy.__must_use_master = self.__must_use_master
        copy.__uuid_subtype = self.__uuid_subtype
        copy.__query_flags = self.__query_flags
        copy.__kwargs = self.__kwargs
        return copy

    def __getitem__(self, index):
        item = pymongo.cursor.Cursor.__getitem__(self, index)

        if isinstance(item, Cursor) or \
           isinstance(item, Document) or \
           self._documentClass is None:
            return item

        return document_factory(self._documentClass, **item)

    def next(self):
        doc = pymongo.cursor.Cursor.next(self)

        if isinstance(doc, Document) or \
           self._documentClass is None:
            return doc

        return document_factory(self._documentClass, **doc)
