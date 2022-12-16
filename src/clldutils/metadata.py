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
import collections
import urllib.parse

import attr

from clldutils import licenses

__all__ = ['Publisher', 'License', 'Metadata']


@attr.s
class Publisher:
    """
    The entity publishing a dataset.

    :ivar name: Name of the publisher.
    :ivar place: Place or address of the publisher, used in "traditional" publisher formats.
    :ivar url: URL linking to the "homepage" of the publisher.
    :ivar contact: An email address under which to contact the publisher of a dataset.
    """
    name = attr.ib(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/name"),
        default=None)
    place = attr.ib(
        metadata=dict(ldkey="dc:Location"),
        default=None)
    url = attr.ib(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/homepage"),
        default=None)
    contact = attr.ib(
        metadata=dict(ldkey="http://xmlns.com/foaf/0.1/mbox"),
        default=None)


@attr.s
class License:
    """
    The license under which a dataset is published, characterized with name, URL and an icon.
    """
    name = attr.ib(
        default="Creative Commons Attribution 4.0 International License")
    url = attr.ib(
        default="https://creativecommons.org/licenses/by/4.0/")
    icon = attr.ib(
        default="cc-by.png")

    def __attrs_post_init__(self):
        lic = licenses.find(self.name)
        if lic:
            self.name = lic.name
            self.url = lic.url


@attr.s
class Metadata:
    """
    Metadata about the published version(s) of a dataset.

    :ivar Publisher publisher: The organisation or institution publishing the dataset.
    :ivar License license: The license under which the dataset can be used.
    :ivar str url: A URL under which the dataset can be browsed.
    :ivar str title: The title of the dataset.
    :ivar str description:
    """
    publisher = attr.ib(default=Publisher(), validator=attr.validators.instance_of(Publisher))
    license = attr.ib(default=License(), validator=attr.validators.instance_of(License))
    url = attr.ib(default=None)
    title = attr.ib(default=None)
    description = attr.ib(default=None)

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
            for f in attr.fields(cls_):
                ckw[f.name] = dd.get(f.metadata.get('ldkey', f.name)) \
                    or defaults.get('{0}.{1}'.format(ldkey.split(':')[1], f.name))
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
            for f in attr.fields(cls_):
                if getattr(obj, f.name):
                    json[f.metadata.get('ldkey', f.name)] = getattr(obj, f.name)
            items.append((ldkey, json))
        return collections.OrderedDict(items)

    @property
    def domain(self):
        return urllib.parse.urlparse(self.url).netloc
