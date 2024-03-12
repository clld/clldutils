"""
This module provides functionality to handle bibliographic metadata, i.e. structured metadata
describing sources of data/research.
"""
import re
import typing
import itertools
import collections

from pylatexenc.latex2text import LatexNodes2Text
from bibtexparser.middlewares import names

__all__ = ['Source']

ID_PATTERN = re.compile(r'^[a-zA-Z\-_0-9]+$')


class Source(collections.OrderedDict):
    """Bibliographic metadata about a source used for some analysis in a linguistic database.

    Following BibTeX-style, a `Source` is just an ordered list of key-value pairs, augmented
    with an id (a.k.a. BibTeX citekey) and a genre (a.k.a. Entry Types).

    :ivar str id: The citekey of a source.
    :ivar str genre: The entry type of a source.

    .. note::

        We restrict the allowed syntax for the id to make sure it can safely be used
        as path component in a URL. To skip this check, pass `_check_id=False` to the
        constructor.

    Usage:

    .. code-block:: python

        >>> from clldutils.source import Source
        >>> src = Source('article', 'Meier2000', author='Meier', year='2000', title='The Title')
        >>> print(src.bibtex())
        @article{Meier2000,
          author = {Meier},
          year   = {2000},
          title  = {The Title}
        }
        >>> print(src)
        Meier. 2000. The Title.
    """

    def __init__(self,
                 genre: str,
                 id_: str,
                 *args,
                 _check_id: bool = True,
                 _lowercase: bool = False,
                 _strip_tex: typing.Optional[typing.Iterable[str]] = None,
                 **kw):
        """
        :param kw: Fields of the bibliographical record as key-value pairs.
        :param _check_id: Flag signaling whether to check the id or not.
        :param _lowercase: Flag signaling whether genre and field names should be lowercased or not.
        :param _strip_tex: `Iterable` of field names for which the value should be stripped from \
        any TeX formatting.
        """
        if _check_id and not ID_PATTERN.match(id_):
            raise ValueError(id_)
        self.genre = genre.lower() if _lowercase else genre
        if _strip_tex:
            _strip_tex = [k.lower() for k in _strip_tex]
            kw = {
                k: LatexNodes2Text().latex_to_text(v) if k.lower() in _strip_tex else v
                for k, v in kw.items()}
        self.id = id_
        super(Source, self).__init__(
            *args, **{k.lower() if _lowercase else k: v for k, v in kw.items()})

    def __bool__(self):  # pragma: no cover
        return True

    __nonzero__ = __bool__

    def __str__(self):
        return self.text()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.id)

    @classmethod
    def from_entry(cls, key: str, entry, **_kw) -> 'Source':
        """
        Factory method to initialize a `Source` instance from a `pybtex.database.Entry`.

        :param key: Citation key, e.g. a key in `pybtex.database.BibliographyData.entries`.
        :param entry: `pybtex.database.Entry`
        :param _kw: Keyword arguments passed through to `cls.__init__`
        """
        _kw.update({k: v for k, v in entry.fields.items()})
        for role in (entry.persons or []):
            if entry.persons[role]:
                _kw[role] = ' and '.join('%s' % p for p in entry.persons[role])
        return cls(entry.type, key, **_kw)

    @classmethod
    def from_bibtex(cls, bibtexString: str, lowercase: bool = False, _check_id: bool = True) \
            -> 'Source':
        """
        Initialize a `Source` object from the data in a BibTeX record.

        .. note::

            We support somewhat limited BibTeX syntax. Thus, it's best to feed preprocessed
            BibTeX (e.g. using a tool such as `bibtool`).
            In particular, we assume all key-value-pairs to be on single lines, i.e. we don't
            support multiline values. Alternatively, you can parse BibTeX data using `pybtex`
            and feed `pybtex.database.Entry` objects to :meth:`Source.from_entry`.
        """
        source = None
        lines = bibtexString.strip().split('\n')

        # genre and key are parsed from the @-line:
        atLine = re.compile(r"^@(?P<genre>[a-zA-Z_]+)\s*{\s*(?P<key>[^,]*)\s*,\s*")

        # since all key-value pairs fit on one line, it's easy to determine the
        # end of the value: right before the last closing brace!
        fieldLine = re.compile(r'\s*(?P<field>[a-zA-Z_]+)\s*=\s*({|")(?P<value>.+)')

        endLine = re.compile(r"}\s*")

        while lines:
            line = lines.pop(0)
            if not source:
                m = atLine.match(line)
                if m:
                    source = cls(
                        m.group('genre').strip().lower(),
                        m.group('key').strip(),
                        _check_id=_check_id)
            else:
                m = fieldLine.match(line)
                if m:
                    value = m.group('value').strip()
                    if value.endswith(','):
                        value = value[:-1].strip()
                    if value.endswith('}') or value.endswith('"'):
                        field = m.group('field')
                        if lowercase:
                            field = field.lower()
                        source[field] = value[:-1].strip()
                else:
                    m = endLine.match(line)
                    if m:
                        break
                    # Note: fields with names not matching the expected pattern are simply
                    # ignored.

        return source

    @staticmethod
    def split_names(s: str) -> typing.List[names.NameParts]:
        return [
            names.parse_single_name_into_parts(name[:-1].strip() if name.endswith(',') else name)
            for name in names.split_multiple_persons_names(s.replace(' & ', ' and '))]

    @staticmethod
    def reformat_names(s: str) -> str:
        res = ''
        names = Source.split_names(s)
        for i, nameparts in enumerate(names):
            if i == 0:
                first = ''
                if nameparts.first:
                    first += ' '.join(nameparts.first)
                if nameparts.von:
                    first += ' {}'.format(' '.join(nameparts.von))
                if nameparts.jr:
                    first += ', {}'.format(' '.join(nameparts.jr))
                res += '{}{}'.format(' '.join(nameparts.last), ', ' + first if first else '')
            else:
                res += ' & ' if i + 1 == len(names) else ', '
                res += nameparts.merge_first_name_first
        return res

    def bibtex(self) -> str:
        """
        Represent the source in BibTeX format.

        :return: string encoding the source in BibTeX syntax.
        """
        m = max(itertools.chain(map(len, self), [0]))
        fields = ("  %s = {%s}" % (k.ljust(m), self[k]) for k in self)
        return "@%s{%s,\n%s\n}" % (
            getattr(self.genre, 'value', self.genre), self.id, ",\n".join(fields))

    _genre_note = {
        'phdthesis': 'dissertation',
        'mastersthesis': 'MA thesis',
        'unpublished': 'unpublished',
    }

    def get_with_translation(self, key):
        res = self.get(key)
        if res and self.get(key + '_english'):
            res = '{0} [{1}]'.format(res, self.get(key + '_english'))
        return res

    @property
    def norm_pages(self):
        return (self.get('pages') or '').replace('--', '–')

    def text(self, markdown=False) -> str:
        """
        Linearize the bib source according to the rules of the unified style.

        :param markdown: If True, italics are used to distinguish volume titles.

        - Book: author. year. booktitle. (series, volume.) address: publisher.
        - Article: author. year. title. journal volume(issue). pages.
        - Incollection: author. year. title. In editor (ed.), booktitle, pages. address: publisher.

        .. seealso::

            `<https://www.linguisticsociety.org/sites/default/files/style-sheet_0.pdf>`_
        """
        def fmt_edition(e):
            try:
                e = int(e)
                return "%d%s" % (e, "tsnrhtdd"[(e // 10 % 10 != 1) * (e % 10 < 4) * e % 10::4])
            except ValueError:  # pragma: no cover
                return e

        def italicized(s):
            if not s:
                return s  # pragma: no cover
            return '_{}_'.format(s) if markdown else s

        genre = getattr(self.genre, 'value', self.genre)
        pages_at_end = genre in (
            'book',
            'phdthesis',
            'mastersthesis',
            'misc',
            'techreport')
        thesis = genre in ('phdthesis', 'mastersthesis')

        if self.get('editor'):
            editors = self['editor'] if self.get('author') else self.reformat_names(self['editor'])
            affix = 'eds' if ' and ' in editors or '&' in editors else 'ed'
            editors = " %s (%s.)" % (editors, affix)
        else:
            editors = None

        res = [
            self.reformat_names(self['author']) if self.get('author') else editors,
            self.get('year', 'n.d')]
        if genre == 'book':  # book title in italics.
            res.append(
                italicized(
                    self.get_with_translation('booktitle') or  # noqa: W504
                    self.get_with_translation('title')))
            series = ', '.join(filter(
                None, [self.get('series'), self.get('volume', self.get('number'))]))
            if series:
                res.append('(%s.)' % series)
        elif genre == 'misc':
            # in case of misc records, we use the note field in case a title is missing.
            res.append(self.get_with_translation('title') or self.get('note'))
        else:  # Dissertation title in italics.
            res.append(
                italicized(self.get_with_translation('title'))
                if genre == 'phdthesis' else self.get_with_translation('title'))

        if genre == 'article':
            # journal in italics!
            atom = ' '.join(filter(None, [italicized(self.get('journal')), self.get('volume')]))
            if self.get('issue') or self.get('number'):
                atom += '(%s)' % (self.get('issue') or self.get('number'))
            res.append(atom)
            if self.get('pages'):
                res.append(self.norm_pages)
            if self.get('doi'):
                res.append('doi: {}'.format(
                    '[{0}](https://doi.org/{0})'.format(self['doi']) if markdown else self['doi']))
        elif genre == 'incollection' or genre == 'inproceedings':
            prefix = 'In'
            atom = ''
            if editors:
                atom += editors
            if self.get('booktitle'):
                if atom:
                    atom += ','
                atom += " %s" % italicized(self.get_with_translation('booktitle'))
            if self.get('pages'):
                atom += ", %s" % self.norm_pages
            res.append(prefix + atom)
        else:
            # check for author to make sure we haven't included the editors yet.
            if editors and self.get('author'):
                res.append("In %s" % editors)

            for attr in [
                'journal',
                'volume' if genre != 'book' else None,
            ]:
                if attr and self.get(attr):
                    res.append(self.get(italicized(attr) if attr == 'journal' else attr))

            if self.get('issue'):
                res.append("(%s)" % self['issue'])

            if not pages_at_end and self.get('pages'):
                res.append(self.norm_pages)

        thesis_handled = False
        if thesis and self.get('school'):
            res.append('{}{} {}'.format(
                '{}: '.format(self['address']) if self.get('address') else '',
                self['school'],
                self._genre_note.get(genre)))
            if self.get('pages'):
                res.append('({}pp.)'.format(self.norm_pages))
            thesis_handled = True
        elif self.get('publisher'):
            if self.get('edition'):
                res.append('{} edn'.format(fmt_edition(self.get('edition'))))
            publisher = self.get('publisher')
            if self.get('address') and publisher.startswith('{}:'.format(self['address'])):
                res.append(self['publisher'])
            else:
                res.append(": ".join(filter(None, [self.get('address'), self['publisher']])))
        else:
            if genre == 'misc' and self.get('howpublished'):
                res.append(self.get('howpublished'))

        if not thesis and pages_at_end and self.get('pages'):
            res.append(self.norm_pages + 'pp')

        if genre != 'article':
            if self.get('doi'):
                res.append('doi: {}'.format(
                    '[{0}](https://doi.org/{0})'.format(self['doi']) if markdown else self['doi']))

        note = self.get('note') or (self._genre_note.get(genre) if not thesis_handled else '')
        if note and note not in res:
            if thesis:
                joiner = ','
                if self.get('pages'):
                    note += '{0} {1}pp.'.format(joiner, self.norm_pages)
            res.append('(%s)' % note)

        return ' '.join(
            x if x.endswith(('.', '.)')) else '%s.' % x for x in res if x).strip()
