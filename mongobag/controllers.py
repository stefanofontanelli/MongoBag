# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from .exc import NoResultFound
from .exc import MultipleResultsFound
from .utils import get_cls_collection
from .utils import set_obj_collection
import logging

__all__ = []

log = logging.getLogger(__file__)


class MongoBase(object):

    def __init__(self, class_, database=None):

        self.class_ = class_
        self.database = database
        self.collection = get_cls_collection(class_)

    def create(self, database=None, manipulate=True, safe=False,
               check_keys=True, continue_on_error=False, opts=None, **kwargs):

        if database is None:
            database = self.database

        if opts is None:
            opts = {}

        collection = database[self.collection]
        obj = self.class_(**kwargs)
        set_obj_collection(obj, collection)
        obj._id = collection.insert(obj.serialize(), manipulate, safe,
                                    check_keys, continue_on_error, **opts)
        return obj

    def read(self, criterion, database=None):

        if database is None:
            database = self.database

        docs = self.search(database, criterion)
        counter = docs.count()

        if counter < 1:
            msg = 'No result for: %s' % criterion
            raise NoResultFound(msg)

        elif counter > 1:
            msg = 'Many results for: %s' % criterion
            raise MultipleResultsFound(msg)

        obj = self.class_(**docs[0])
        set_obj_collection(obj, database[self.collection])

        return obj

    def search(self, database=None,
               criterion=None, sort=None, start=None, limit=None):

        if database is None:
            database = self.database

        if start is None:
            start = 0

        if limit is None:
            limit = 0

        collection = database[self.collection]
        docs = collection.find(criterion, skip=start, limit=limit, sort=sort)

        return docs

    def update(self, database=None, **kwargs):

        if database is None:
            database = self.database

        if '_id' not in kwargs:
            raise TypeError('You must provide an ObjectId.')

        obj = self.class_(**kwargs)
        obj.save(self.database)

        return obj

    def delete(self, database=None, **kwargs):

        if database is None:
            database = self.database

        if '_id' not in kwargs:
            raise TypeError('You must provide an ObjectId.')

        obj = self.class_(**kwargs)
        obj.delete(self.database)