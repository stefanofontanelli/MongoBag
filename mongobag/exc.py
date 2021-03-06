# Copyright (C) 2012 the MongoBag authors and contributors
# <see AUTHORS file>
#
# This module is part of MongoBag and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php


class NoResultFound(Exception):
    """This exception must be raised when a query returns no results.
    """


class MultipleResultsFound(Exception):
    """ This exception must be raised when a query returns multiple results
        instead of one.
    """


class DocumentAttributeError(AttributeError):
    """ This exception must be raised when document's __setattr__ and __init__
        receive a value which has wrong type.
    """


class DocumentTypeError(TypeError):
    """ This exception must be raised when document's __setattr__ and __init__
        receive a value which has wrong type.
    """
