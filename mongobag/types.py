# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import bson
import colander
import logging

__all__ = []

log = logging.getLogger(__file__)


class ObjectId(colander.String):

    def serialize(self, node, appstruct):

        if appstruct is colander.null:
            return colander.null

        if not isinstance(appstruct, bson.objectid.ObjectId):
            raise colander.Invalid(node, '%r is not an ObjectId')

        return str(appstruct)

    def deserialize(self, node, cstruct):

        if cstruct is colander.null:
            return bson.objectid.ObjectId()

        try:
            objectid = bson.objectid.ObjectId(str(cstruct))

        except (TypeError, bson.errors.InvalidId):
            msg = '%s is not a valid ObjectId' % cstruct
            raise colander.Invalid(node, msg)
        else:
            return objectid
