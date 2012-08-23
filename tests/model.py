from mongobag import Boolean
from mongobag import Date
from mongobag import DateTime
from mongobag import Document
from mongobag import EmbeddedDocument
from mongobag import EmbeddedList
from mongobag import Float
from mongobag import Integer
from mongobag import String
from mongobag import Time
import colander


class DummyDocument(Document):

    __collection__ = 'dummydocument'

    name = String()


class MainDocument(Document):

    __collection__ = 'maindocument'

    string = String()
    integer = Integer()
    boolean = Boolean()
    float = Float()
    datetime = DateTime()
    date = Date()
    time = Time()
    ed = EmbeddedDocument(DummyDocument)
    edl = EmbeddedList(DummyDocument)


class MixinDocument(DummyDocument, MainDocument):
    mixinfield = String()


DummyDocument.description = String(missing=colander.null, default=colander.null)


class Group(Document):

    __collection__ = 'groups'

    name = String()


class Account(Document):

    __collection__ = 'accounts'

    name = String()
    surname = String()
    username = String()
    password = String()
    groups = EmbeddedList(Group, missing=list, default=list)


class MenuItem(Document):
    label = String()
    url = String()
    # children = EmbeddedList(MenuItem)


MenuItem.children = EmbeddedList(MenuItem)


class Language(Document):
    name = String()
    code = String(validator=colander.Length(min=2, max=2))
    country = String(validator=colander.Length(min=2, max=2))


class MenuTranslation(Document):
    language = EmbeddedDocument(Language)
    items = EmbeddedList(MenuItem)


class Menu(Document):
    name = String()
    translations = EmbeddedList(MenuTranslation)


# Module
class ModuleLabel(Document):
    language = EmbeddedDocument(Language)
    name = String()


class ModuleFunctionArg(Document):
    name = String(validator=None)  # PythonIdentifier
    default = String(missing=None, default=None)  # Raw


class ModuleFunction(Document):
    name = String(validator=None)  # PythonIdentifier
    args = EmbeddedList(ModuleFunctionArg)


class Module(Document):
    module = String()  # DottedPythonName
    labels = EmbeddedList(ModuleLabel)
    functions = EmbeddedList(ModuleFunction)
    # assets ?


# Page

CHANGEFREQ = ('always', 'hourly', 'daily', 'weekly',
              'monthly', 'yearly', 'never')


class Sitemap(Document):

    priority = Float(validator=colander.Range(min=0.0, max=1.0),
                     default=0.5,
                     missing=0.5)
    lastmod = DateTime(default=None, missing=None)
    changefreq = String(validator=colander.OneOf(CHANGEFREQ),
                        default=None,
                        missing=None)

# Node/Url of contents.


class Url(Document):

    __collection__ = 'urls'

    url = String()  # validator=Path
    enabled = Boolean(default=False)


# Page


class MetaAttr(Document):

    key = String()
    value = String()


class Meta(Document):

    attrs = EmbeddedList(MetaAttr)
    value = String(default='', missing='')


class Head(Document):

    meta = EmbeddedList(Meta)


class Content(Document):

    body = String()  # preparer=clean_html


class PageTranslation(Document):

    language = EmbeddedDocument(Language)
    url = String()  # validator=Path


class Page(Url):

    head = EmbeddedDocument(Head)
    title = String(default=None)
    template = String(default=None)
    language = EmbeddedDocument(Language)
    contents = EmbeddedList(Content)
    translations = EmbeddedList(PageTranslation, missing=[], default=[])
    sitemap = EmbeddedDocument(Sitemap, missing={}, default={})
    homepage = Boolean(default=False)


# Redirect

class Redirect(Url):

    code = Integer(validator=colander.Range(300, 308))
    location = String()  # validator=URI
