"""
Support for standard dataset/app metadata
"""
import collections
import urllib.parse

import attr

__all__ = ['Publisher', 'License', 'Metadata']


@attr.s
class Publisher:
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
    name = attr.ib(
        default="Creative Commons Attribution 4.0 International License")
    url = attr.ib(
        default="https://creativecommons.org/licenses/by/4.0/")
    icon = attr.ib(
        default="cc-by.png")


@attr.s
class Metadata:
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

    def to_jsonld(self):
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
