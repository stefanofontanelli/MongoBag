from mongobag import Boolean
from mongobag import Date
from mongobag import DateTime
from mongobag import Decimal
from mongobag import DocumentMeta
from mongobag import EmbeddedDocumentMeta
from mongobag import Float
from mongobag import GlobalObject
from mongobag import Integer
from mongobag import Mapping
from mongobag import ObjectId
from mongobag import Sequence
from mongobag import String
from mongobag import Time
from mongobag import Tuple
import colander


class MainEmbeddedDocument(object):

    __metaclass__ = EmbeddedDocumentMeta
    string = String()
    integer = Integer()
    boolean = Boolean()
    float = Float()
    decimal = Decimal()
    datetime = DateTime()
    date = Date()
    time = Time()
    colander = GlobalObject(colander)


class MainDocument(object):

    __metaclass__ = DocumentMeta
    _id = ObjectId()
    mapping = Mapping(MainEmbeddedDocument)
    tuple = Tuple(MainEmbeddedDocument)
    sequence = Sequence(MainEmbeddedDocument)
