# coding: utf8
"""
Functionality to read and write metadata for CSV files.

This module implements (partially) the W3C recommendation
"Metadata Vocabulary for Tabular Data".

.. seealso:: https://www.w3.org/TR/tabular-metadata/
"""
from __future__ import unicode_literals, print_function, division
import re
from collections import OrderedDict

from six import text_type
import attr
from uritemplate import URITemplate as _URITemplate

from clldutils.dsv import Dialect, reader
from clldutils.jsonlib import load, dump
from clldutils.path import Path
from clldutils.misc import UnicodeMixin, cached_property
from clldutils import attrlib
from clldutils.csvw.datatypes import DATATYPES

# Level 1 variable names according to https://tools.ietf.org/html/rfc6570#section-2.3:
_varchar = '([a-zA-Z0-9_]|\%[a-fA-F0-9]{2})'
_varname = re.compile('(' + _varchar + '([.]?' + _varchar + ')*)$')


class URITemplate(_URITemplate):
    def __eq__(self, other):
        if not hasattr(other, 'uri'):
            return False
        return _URITemplate.__eq__(self, other)  # pragma: no cover

    def asdict(self, **kw):
        return '{0}'.format(self)


def uri_template_property():
    """
    Note: We do not currently provide support for supplying the "_" variables like "_row"
    when expanding a URI template.

    .. seealso:: http://w3c.github.io/csvw/metadata/#uri-template-properties
    """
    return attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(URITemplate)),
        convert=lambda v: v if v is None else URITemplate(v))


class Link(UnicodeMixin):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#link-properties
    """
    def __init__(self, string):
        self.string = string

    def __unicode__(self):
        return self.string

    def asdict(self, omit_defaults=True):
        return self.string

    def __eq__(self, other):
        # FIXME: Only naive, un-resolved comparison is supported at the moment.
        return self.string == other.string if isinstance(other, Link) else False

    def resolve(self, base):
        if not base:
            return self.string
        if isinstance(base, Path):
            return base.joinpath(self.string)
        if not base.endswith('/'):
            base += '/'
        return base + self.string


def link_property():
    return attr.ib(
        default=None,
        validator=attr.validators.instance_of(Link),
        convert=lambda v: Link(v))


class NaturalLanguage(UnicodeMixin, OrderedDict):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#natural-language-properties
    """
    def __init__(self, value):
        OrderedDict.__init__(self)
        self.value = value
        if isinstance(self.value, text_type):
            self[None] = [self.value]
        elif isinstance(self.value, (list, tuple)):
            self[None] = list(self.value)
        elif isinstance(self.value, (dict, OrderedDict)):
            for k, v in self.value.items():
                if not isinstance(v, (list, tuple)):
                    v = [v]
                self[k] = v
        else:
            raise ValueError('invalid value type for NaturalLanguage')

    def asdict(self, omit_defaults=True):
        if list(self.keys()) == [None]:
            if len(self[None]) == 1:
                return self.getfirst()
            return self[None]
        return OrderedDict(
            [('und' if k is None else k, v[0] if len(v) == 1 else v)
             for k, v in self.items()])

    def add(self, string, lang=None):
        if lang not in self:
            self[lang] = []
        self[lang].append(string)

    def __unicode__(self):
        return self.getfirst() or list(self.values())[0][0]

    def getfirst(self, lang=None):
        return self.get(lang, [None])[0]


@attr.s
class DescriptionBase(object):
    """
    Container for
    - common properties (see http://w3c.github.io/csvw/metadata/#common-properties)
    - @-properies.
    """
    common_props = attr.ib(default=attr.Factory(dict))
    at_props = attr.ib(default=attr.Factory(dict))

    @staticmethod
    def partition_properties(d):
        c, a, dd = {}, {}, {}
        for k, v in (d or {}).items():
            if k.startswith('@'):
                a[k[1:]] = v
            elif ':' in k:
                c[k] = v
            else:
                dd[k] = v
        return dict(common_props=c, at_props=a, **dd)

    @classmethod
    def fromvalue(cls, d):
        return cls(**cls.partition_properties(d))

    def _iter_dict_items(self, omit_defaults):
        def _asdict_single(v):
            return v.asdict(omit_defaults=omit_defaults) if hasattr(v, 'asdict') else v

        def _asdict_multiple(v):
            if isinstance(v, (list, tuple)):
                return [_asdict_single(vv) for vv in v]
            return _asdict_single(v)

        for k, v in sorted(self.at_props.items()):
            yield '@' + k, _asdict_multiple(v)

        for k, v in sorted(self.common_props.items()):
            yield k, _asdict_multiple(v)

        for k, v in attrlib.asdict(self, omit_defaults=omit_defaults).items():
            if k not in ['common_props', 'at_props']:
                yield k, _asdict_multiple(v)

    def asdict(self, omit_defaults=True):
        return OrderedDict(
            [(k, v) for k, v in
             self._iter_dict_items(omit_defaults) if v not in [None, [], {}]])


def optional_int():
    return attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
        convert=lambda v: v if v is None else int(v))


@attr.s
class Datatype(DescriptionBase):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#datatypes
    """
    base = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(DATATYPES)))
    format = attr.ib(default=None)
    length = optional_int()
    minLength = optional_int()
    maxLength = optional_int()
    minimum = attr.ib(default=None)
    maximum = attr.ib(default=None)
    minInclusive = attr.ib(default=None)
    maxInclusive = attr.ib(default=None)
    minExclusive = attr.ib(default=None)
    maxExclusive = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.length is not None:
            if self.minLength is not None and self.length < self.minLength:
                raise ValueError()

            if self.maxLength is not None:
                if self.length > self.maxLength:
                    raise ValueError()

        if self.minLength is not None and self.maxLength is not None \
                and self.minLength > self.maxLength:
            raise ValueError()

        if not isinstance(self.derived_description, dict):
            raise ValueError()  # pragma: no cover

    @classmethod
    def fromvalue(cls, v):
        """
        either a single string that is the main datatype of the values of the cell or a
        datatype description object.
        """
        if isinstance(v, cls):
            return v

        if isinstance(v, text_type):
            return cls(base=v)

        if isinstance(v, (dict, OrderedDict)):
            return cls(**DescriptionBase.partition_properties(v))

        raise ValueError(v)

    def asdict(self, omit_defaults=True):
        res = DescriptionBase.asdict(self, omit_defaults=omit_defaults)
        if len(res) == 1 and 'base' in res:
            return res['base']
        return res

    @property
    def basetype(self):
        return DATATYPES[self.base]

    @property
    def derived_description(self):
        return self.basetype.derived_description(self)

    def formatted(self, v):
        return self.basetype.to_string(v, **self.derived_description)

    def parse(self, v):
        return self.basetype.to_python(v, **self.derived_description)

    def validate(self, v):
        try:
            l = len(v or '')
            if self.length is not None and l != self.length:
                raise ValueError()
            if self.minLength is not None and l < self.minLength:
                raise ValueError()
            if self.maxLength is not None and l > self.maxLength:
                raise ValueError()
        except TypeError:
            pass
        if self.basetype.minmax:
            if self.minimum is not None and v < self.minimum:
                raise ValueError()
            if self.maximum is not None and v > self.maximum:
                raise ValueError()
        return v

    def read(self, v):
        return self.validate(self.parse(v))


@attr.s
class Description(DescriptionBase):
    """
    Adds support for inherited properties.

    .. seealso:: http://w3c.github.io/csvw/metadata/#inherited-properties
    """
    # To be able to resolve inheritance chains, we also provide a place to store a
    # reference to the containing object:
    _parent = attr.ib(default=None, repr=False)

    aboutUrl = uri_template_property()
    datatype = attr.ib(
        default=None,
        convert=lambda v: v if not v else Datatype.fromvalue(v))
    default = attr.ib(default="")
    lang = attr.ib(default="und")
    null = attr.ib(default="")
    ordered = attr.ib(default=None)
    propertyUrl = uri_template_property()
    required = attr.ib(default=None)
    separator = attr.ib(default=None)
    textDirection = attr.ib(default=None)
    valueUrl = uri_template_property()

    def inherit(self, attr):
        v = getattr(self, attr)
        if v is None and self._parent:
            return getattr(self._parent, attr)
        return v


@attr.s
class Column(UnicodeMixin, Description):
    name = attr.ib(
        default=None,
        validator=attrlib.valid_re(_varname, nullable=True))
    suppressOutput = attr.ib(default=False)
    titles = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(NaturalLanguage)),
        convert=lambda v: v if v is None else NaturalLanguage(v))
    virtual = attr.ib(default=False)
    _number = attr.ib(default=None, repr=False)

    def __unicode__(self):
        return self.name or \
            (self.titles and self.titles.getfirst()) or \
            '_col.{0}'.format(self._number)


def column_reference():
    return attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(list)),
        convert=lambda v: v if isinstance(v, list) else [v])


@attr.s
class Reference(object):
    resource = link_property()
    schemaReference = link_property()
    columnReference = column_reference()


@attr.s
class ForeignKey(object):
    columnReference = column_reference()
    reference = attr.ib(default=None)

    @classmethod
    def fromdict(cls, d):
        d['reference'] = Reference(**d['reference'])
        return cls(**d)

    def asdict(self, **kw):
        res = attrlib.asdict(self, **kw)
        res['reference'] = attrlib.asdict(res['reference'], **kw)
        return res


@attr.s
class Schema(Description):
    columns = attr.ib(
        default=attr.Factory(list),
        convert=lambda v: [Column.fromvalue(c) for c in v])
    foreignKeys = attr.ib(
        default=attr.Factory(list),
        convert=lambda v: [] if v is None else [ForeignKey.fromdict(d) for d in v])
    primaryKey = attr.ib(default=None)
    rowTitles = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        for i, col in enumerate(self.columns):
            col._parent = self
            col._number = i + 1


@attr.s
class TableLike(Description):
    dialect = attr.ib(
        default=None, convert=lambda v: Dialect(**v) if isinstance(v, dict) else v)
    notes = attr.ib(default=attr.Factory(list))
    tableDirection = attr.ib(
        default='auto',
        validator=attr.validators.in_(['rtl', 'ltr', 'auto']))
    tableSchema = attr.ib(
        default=None,
        convert=lambda v: Schema.fromvalue(v))
    transformations = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        if self.tableSchema:
            self.tableSchema._parent = self


@attr.s
class Table(TableLike):
    url = link_property()
    suppressOutput = attr.ib(default=False)

    @property
    def local_name(self):
        return self.url.string

    @cached_property()
    def colspec(self):
        spec = {}
        for col in self.tableSchema.columns:
            desc = Description(**{
                attr: col.inherit(attr)
                for attr in ['datatype', 'lang', 'null', 'required', 'separator']})
            desc = ('{0}'.format(col), desc)
            spec['{0}'.format(col)] = desc
            if col.titles:
                spec.setdefault(col.titles.getfirst(), desc)
        return spec

    def __iter__(self):
        dialect = self.dialect or self._parent.dialect or Dialect()
        fname = self.url.resolve(self._parent.base)

        if dialect.header:
            items = reader(fname, dialect=dialect, dicts=True)
        else:
            header = [
                '{0}'.format(col) for col in self.tableSchema.columns if not col.virtual]
            items = [
                OrderedDict(zip(header, row)) for row in reader(fname, dialect=dialect)]

        for item in items:
            res = OrderedDict()
            for k, v in item.items():
                # see http://w3c.github.io/csvw/syntax/#parsing-cells
                name, spec = self.colspec.get(k, (None, None))
                if name:
                    k = name
                if spec:
                    if v == '':
                        if spec.required:
                            raise ValueError('required column value is missing')
                        v = spec.default

                    if spec.separator:
                        if v == '':
                            v = []
                        else:
                            if v == spec.null:
                                v = None
                            else:
                                v = v.split(spec.separator)
                                v = [spec.default if vv is '' else vv for vv in v]
                                v = [None if vv == spec.null else vv for vv in v]
                    else:
                        if v == spec.null:
                            if spec.required:
                                raise ValueError('required column value is missing')
                            v = None

                    if spec.datatype:
                        if isinstance(v, list):
                            v = [spec.datatype.read(vv) for vv in v]
                        else:
                            v = spec.datatype.read(v)
                res[k] = v
            yield res


@attr.s
class TableGroup(TableLike):
    _fname = attr.ib(default=None)
    url = attr.ib(default=None)
    tables = attr.ib(
        repr=False,
        default=attr.Factory(list),
        convert=lambda v: [Table.fromvalue(vv) for vv in v])

    def __attrs_post_init__(self):
        TableLike.__attrs_post_init__(self)
        for table in self.tables:
            table._parent = self

    @property
    def tabledict(self):
        return {t.local_name: t for t in self.tables}

    def check_referential_integrity(self):
        data = {}
        for n, table in self.tabledict.items():
            data[n] = list(table)

        for n, table in self.tabledict.items():
            for fk in table.tableSchema.foreignKeys:
                for item in data[n]:
                    colref = [item[k] for k in fk.columnReference]
                    for ref in data[fk.reference.resource.string]:
                        key = [ref[k] for k in fk.reference.columnReference]
                        if key == colref:
                            break
                    else:
                        raise ValueError('Key {0} not found in table {1}'.format(
                            colref, fk.reference.resource.string))

    #
    # FIXME: to_sqlite()!
    #

    @property
    def base(self):
        return self._fname.parent

    @classmethod
    def from_file(cls, fname):
        res = cls.fromvalue(load(fname))
        res._fname = Path(fname)
        return res

    def to_file(self, fname, omit_defaults=True):
        dump(self.asdict(omit_defaults=omit_defaults), fname, indent=4)
        return fname
