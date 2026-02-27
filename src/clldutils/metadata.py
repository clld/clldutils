"""
JSON-LD - the serialization format used for metadata in CLDF datasets - supports nested data.
To make creating (and reading) this data simpler, this module provides a Python API to build data
structures which "know" how to read from/serialize to JSON-LD.

Usage:

.. code-block:: python

    >>> from clldutils.metadata import *
    >>> md = Metadata(
    ...     title='The Data',
    ...     publisher=Publisher(name='Data Press', place='anywhere'),
    ...     license=License(name='CC-BY-4.0'))
    >>> md.to_jsonld()['dc:license']
    OrderedDict([('name', 'Creative Commons Attribution 4.0'),
                 ('url', 'https://creativecommons.org/licenses/by/4.0/'),
                 ('icon', 'cc-by.png')])
    >>> Metadata.from_jsonld(md.to_jsonld()).publisher.place
    'anywhere'
"""
from typing import Optional
import collections
import dataclasses
import urllib.parse

from clldutils import licenses

__all__ = ['Publisher', 'License', 'Metadata']


@dataclasses.dataclass
class Publisher:
    """
    The entity publishing a dataset.

    :ivar name: Name of the publisher.
    :ivar place: Place or address of the publisher, used in "traditional" publisher formats.
    :ivar url: URL linking to the "homepage" of the publisher.
    :ivar contact: An email address under which to contact the publisher of a dataset.
    """
    name: Optional[str] = dataclasses.field(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/name"),
        default=None)
    place: Optional[str] = dataclasses.field(
        metadata=dict(ldkey="dc:Location"),
        default=None)
    url: Optional[str] = dataclasses.field(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/homepage"),
        default=None)
    contact: Optional[str] = dataclasses.field(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/mbox"),
        default=None)


@dataclasses.dataclass
class License:
    """
    The license under which a dataset is published, characterized with name, URL and an icon.
    """
    name: Optional[str] = "Creative Commons Attribution 4.0 International License"
    url: Optional[str] = "https://creativecommons.org/licenses/by/4.0/"
    icon: Optional[str] = "cc-by.png"

    def __post_init__(self):
        lic = licenses.find(self.name)
        if lic:
            self.name = lic.name
            self.url = lic.url


@dataclasses.dataclass
class Metadata:
    """
    Metadata about the published version(s) of a dataset.

    :ivar Publisher publisher: The organisation or institution publishing the dataset.
    :ivar License license: The license under which the dataset can be used.
    :ivar str url: A URL under which the dataset can be browsed.
    :ivar str title: The title of the dataset.
    :ivar str description:
    """
    publisher: Publisher = dataclasses.field(default_factory=Publisher)
    license: License = dataclasses.field(default_factory=License)
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_jsonld(cls, d, defaults=None):
        defaults = defaults or {}
        kw = {}
        for k, v in [
            ('dcat:accessURL', 'url'),
            ('dc:title', 'title'),
            ('dc:description', 'description'),
        ]:
            val = d.get(k) or defaults.get(v)
            if val:
                kw[v] = val
        for ldkey, cls_ in [('dc:publisher', Publisher), ('dc:license', License)]:
            ckw = {}
            dd = d.get(ldkey, {})
            for f in dataclasses.fields(cls_):
                val = dd.get(f.metadata.get('ldkey', f.name))
                ckw[f.name] = val or defaults.get(f"{ldkey.split(':')[1]}.{f.name}")
            kw[cls_.__name__.lower()] = cls_(**{k: v for k, v in ckw.items() if v})
        return cls(**kw)

    def to_jsonld(self) -> collections.OrderedDict:
        """
        Returns a `dict` suitable for serialization as JSON-LD object, with the metadata tagged
        with suitable common properties.
        """
        items = [("@context", ["http://www.w3.org/ns/csvw", {"@language": "en"}])]
        for k, v in [
            ('dcat:accessURL', 'url'),
            ('dc:title', 'title'),
            ('dc:description', 'description'),
        ]:
            if getattr(self, v):
                items.append((k, getattr(self, v)))
        for ldkey, cls_ in [('dc:publisher', Publisher), ('dc:license', License)]:
            obj = getattr(self, ldkey.split(':')[1])
            json = collections.OrderedDict()
            for f in dataclasses.fields(cls_):
                if getattr(obj, f.name):
                    json[f.metadata.get('ldkey', f.name)] = getattr(obj, f.name)
            items.append((ldkey, json))
        return collections.OrderedDict(items)

    @property
    def domain(self):
        return urllib.parse.urlparse(self.url).netloc
