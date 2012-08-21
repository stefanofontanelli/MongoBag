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
import colander


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


DummyDocument.description = String(missing=colander.null, default=colander.null)


class Group(Document):

    name = String()


class Account(Document):

    name = String()
    surname = String()
    username = String()
    password = String()
    #groups = EmbeddedList(Group, missing=list, default=list)


class MenuItem(Document):
    label = String()
    url = String()
    #children = EmbeddedList(MenuItem)


# Avoid circular dep.
MenuItem.children = EmbeddedList(MenuItem)


class MenuTranslation(Document):
    language = String()
    items = EmbeddedList(MenuItem)


class Menu(Document):
    name = String()
    translations = EmbeddedList(MenuTranslation)
