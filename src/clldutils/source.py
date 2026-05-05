"""
This module provides functionality to handle bibliographic metadata, i.e. structured metadata
describing sources of data/research.
"""
import re
from typing import Optional
import itertools
import collections
from collections.abc import Iterable

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
                 _strip_tex: Optional[Iterable[str]] = None,
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
        super().__init__(*args, **{k.lower() if _lowercase else k: v for k, v in kw.items()})

    def __bool__(self):  # pragma: no cover
        return True

    __nonzero__ = __bool__

    def __str__(self):
        return self.text()

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'

    @classmethod
    def from_entry(cls, key: str, entry, **_kw) -> 'Source':
        """
        Factory method to initialize a `Source` instance from a `pybtex.database.Entry`.

        :param key: Citation key, e.g. a key in `pybtex.database.BibliographyData.entries`.
        :param entry: `pybtex.database.Entry`
        :param _kw: Keyword arguments passed through to `cls.__init__`
        """
        _kw.update(entry.fields.items())
        for role in (entry.persons or []):
            if entry.persons[role]:
                _kw[role] = ' and '.join(str(p) for p in entry.persons[role])
        return cls(entry.type, key, **_kw)

    @classmethod
    def from_bibtex(
            cls,
            bibtex_string: str,
            lowercase: bool = False,
            _check_id: bool = True,
    ) -> 'Source':
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
        lines = bibtex_string.strip().split('\n')

        # genre and key are parsed from the @-line:
        at_line = re.compile(r"^@(?P<genre>[a-zA-Z_]+)\s*{\s*(?P<key>[^,]*)\s*,\s*")

        # since all key-value pairs fit on one line, it's easy to determine the
        # end of the value: right before the last closing brace!
        field_line = re.compile(r'\s*(?P<field>[a-zA-Z_]+)\s*=\s*({|")(?P<value>.+)')

        end_line = re.compile(r"}\s*")

        while lines:
            line = lines.pop(0)
            if not source:
                m = at_line.match(line)
                if m:
                    source = cls(
                        m.group('genre').strip().lower(),
                        m.group('key').strip(),
                        _check_id=_check_id)
            else:
                m = field_line.match(line)
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
                    m = end_line.match(line)
                    if m:
                        break
                    # Note: fields with names not matching the expected pattern are simply
                    # ignored.

        return source

    @staticmethod
    def split_names(s: str) -> list[names.NameParts]:
        """Splits string like author lists."""
        def _split(ss):
            return [
                names.parse_single_name_into_parts(n[:-1].strip() if n.endswith(',') else n)
                for n in names.split_multiple_persons_names(ss.replace(' & ', ' and '))]

        try:
            return _split(s)
        except names.InvalidNameError:  # pragma: no cover
            # Fix initials which are not properly terminated.
            # e.g "Hall, T. A and Hildebrandt, Kristine A and Bickel, Balthasar"
            return _split(re.sub('(?P<initial>[A-Z]) ', lambda m: f"{m.group('initial')}. ", s))

    @staticmethod
    def reformat_names(s: str) -> str:
        """
        Reformats names using <first last> format.

        .. code-block:: python

            >>> Source.reformat_names('Max Meier and Müller, Hans')
            'Meier, Max & Hans Müller'
        """
        res = ''
        names_ = Source.split_names(s)
        for i, nameparts in enumerate(names_):
            if i == 0:
                first = ''
                if nameparts.first:
                    first += ' '.join(nameparts.first)
                if nameparts.von:
                    first += f" {' '.join(nameparts.von)}"
                if nameparts.jr:
                    first += f", {' '.join(nameparts.jr)}"
                res += f"{' '.join(nameparts.last)}{', ' + first if first else ''}"
            else:
                res += ' & ' if i + 1 == len(names_) else ', '
                res += nameparts.merge_first_name_first
        return res

    def bibtex(self) -> str:
        """
        Represent the source in BibTeX format.

        :return: string encoding the source in BibTeX syntax.
        """
        m = max(itertools.chain(map(len, self), [0]))
        fields = ',\n'.join(f"  {k.ljust(m)} = {{{self[k]}}}" for k in self)
        genre = getattr(self.genre, 'value', self.genre)
        return f"@{genre}{{{self.id},\n{fields}\n}}"

    _genre_note = {
        'phdthesis': 'dissertation',
        'mastersthesis': 'MA thesis',
        'unpublished': 'unpublished',
    }

    def get_with_translation(self, key: str) -> str:
        """Return the value for a key, possibly with an english translation."""
        res = self.get(key)
        if res and self.get(key + '_english'):
            res = f'{res} [{self.get(key + "_english")}]'
        return res

    @property
    def norm_pages(self) -> str:
        """Replace the LaTeX double-hyphen used for page ranges with single hyphen."""
        return (self.get('pages') or '').replace('--', '–')

    @staticmethod
    def _fmt_edition(e):
        try:
            e = int(e)
            return "%d%s" % (  # pylint: disable=consider-using-f-string
                e, "tsnrhtdd"[(e // 10 % 10 != 1) * (e % 10 < 4) * e % 10::4])
        except ValueError:  # pragma: no cover
            return e

    @staticmethod
    def _italicized(s, markdown):
        if not s:
            return s  # pragma: no cover
        return f'_{s}_' if markdown else s

    @staticmethod
    def _doi(s, markdown):
        doi_ = f'[{s}](https://doi.org/{s})' if markdown else s
        return f'doi: {doi_}'

    def text(self, markdown=False) -> str:  # pylint: disable=too-many-branches
        """
        Linearize the bib source according to the rules of the unified style.

        :param markdown: If True, italics are used to distinguish volume titles.

        - Book: author. year. booktitle. (series, volume.) address: publisher.
        - Article: author. year. title. journal volume(issue). pages.
        - Incollection: author. year. title. In editor (ed.), booktitle, pages. address: publisher.

        .. seealso::

            `<https://www.linguisticsociety.org/sites/default/files/style-sheet_0.pdf>`_
        """
        genre = getattr(self.genre, 'value', self.genre)
        pages_at_end = genre in ('book', 'phdthesis', 'mastersthesis', 'misc', 'techreport')
        thesis = genre in ('phdthesis', 'mastersthesis')

        editors = None
        if self.get('editor'):
            editors = self['editor'] if self.get('author') else self.reformat_names(self['editor'])
            affix = 'eds' if ' and ' in editors or '&' in editors else 'ed'
            editors = f" {editors} ({affix}.)"

        res = [
            self.reformat_names(self['author']) if self.get('author') else editors,
            self.get('year', 'n.d')]
        self._format_title(res, markdown, genre)

        if genre == 'article':
            self._format_article(res, markdown)
        elif genre in {'incollection', 'inproceedings', 'inbook'}:
            self._format_in(res, markdown, editors)
        else:
            self._format_rest(res, markdown, genre, editors, pages_at_end)

        thesis_handled = False
        if thesis and self.get('school'):
            res.append('{}{} {}'.format(  # pylint: disable=consider-using-f-string
                f"{self['address']}: " if self.get('address') else '',
                self['school'],
                self._genre_note.get(genre)))
            if self.get('pages'):
                res.append(f'({self.norm_pages}pp.)')
            thesis_handled = True
        elif self.get('publisher'):
            if self.get('edition'):
                res.append(f"{self._fmt_edition(self.get('edition'))} edn")
            publisher = self.get('publisher')
            if self.get('address') and publisher.startswith(f"{self['address']}:"):
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
                res.append(self._doi(self['doi'], markdown))

        note = self.get('note') or (self._genre_note.get(genre) if not thesis_handled else '')
        if note and note not in res:
            if thesis:
                joiner = ','
                if self.get('pages'):
                    note += f'{joiner} {self.norm_pages}pp.'
            res.append(f'({note})')

        return ' '.join(x if x.endswith(('.', '.)')) else f'{x}.' for x in res if x).strip()

    def _format_title(self, res, markdown, genre):
        if genre == 'book':  # book title in italics.
            res.append(
                self._italicized(
                    self.get_with_translation('booktitle') or  # noqa: W504
                    self.get_with_translation('title'),
                    markdown))
            series = ', '.join(filter(
                None, [self.get('series'), self.get('volume', self.get('number'))]))
            if series:
                res.append(f'({series}.)')
        elif genre == 'misc':
            # in case of misc records, we use the note field in case a title is missing.
            res.append(self.get_with_translation('title') or self.get('note'))
        else:  # Dissertation title in italics.
            res.append(
                self._italicized(self.get_with_translation('title'), markdown)
                if genre == 'phdthesis' else self.get_with_translation('title'))

    def _format_article(self, res, markdown):
        # journal in italics!
        atom = ' '.join(
            filter(None, [self._italicized(self.get('journal'), markdown), self.get('volume')]))
        if self.get('issue') or self.get('number'):
            atom += f"({self.get('issue') or self.get('number')})"
        res.append(atom)
        if self.get('pages'):
            res.append(self.norm_pages)
        if self.get('doi'):
            res.append(self._doi(self['doi'], markdown))

    def _format_in(self, res, markdown, editors):
        prefix = 'In'
        atom = ''
        if editors:
            atom += editors
        if self.get('booktitle'):
            if atom:
                atom += ','
            atom += f" {self._italicized(self.get_with_translation('booktitle'), markdown)}"
        if self.get('pages'):
            atom += f", {self.norm_pages}"
        if atom:
            res.append(prefix + atom)

    def _format_rest(  # pylint: disable=R0913,R0917
            self, res, markdown, genre, editors, pages_at_end):
        # check for author to make sure we haven't included the editors yet.
        if editors and self.get('author'):
            res.append(f"In {editors}")

        for attr in [
            'journal',
            'volume' if genre != 'book' else None,
        ]:
            if attr and self.get(attr):
                res.append(self.get(
                    self._italicized(attr, markdown) if attr == 'journal' else attr))

        if self.get('issue'):
            res.append(f"({self['issue']})")

        if not pages_at_end and self.get('pages'):  # pragma: no cover
            res.append(self.norm_pages)
