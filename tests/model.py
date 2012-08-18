from mongobag import Boolean
from mongobag import Date
from mongobag import DateTime
from mongobag import Document
from mongobag import DocumentMetaClass
from mongobag import Embedded
from mongobag import EmbeddedList
from mongobag import Float
from mongobag import Integer
from mongobag import String
from mongobag import Time


class DummyDocument(Document):

    name = String()


class MainDocument(Document):

    string = String()
    integer = Integer()
    boolean = Boolean()
    float = Float()
    datetime = DateTime()
    date = Date()
    time = Time()
    #embedded = Embedded(DummyDocument, missing=None)
    #embedded_list = EmbeddedList(DummyDocument, missing=list)


class MixinDocument(DummyDocument, MainDocument):
    mixinfield = String()


DummyDocument.description = String()


class Group(Document):

    name = String()


class Account(Document):

    name = String()
    surname = String()
    username = String()
    password = String()
    #groups = EmbeddedList(Group, missing=list, default=list)
