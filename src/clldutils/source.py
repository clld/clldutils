import re
import itertools
import collections

ID_PATTERN = re.compile('^[a-zA-Z\-_0-9]+$')


class Source(collections.OrderedDict):
    """Bibliographic metadata about a source used for some analysis in a linguistic database.

    Following BibTeX-style, a Source is just an ordered list of key-value pairs, augmented
    with an id (a.k.a. BibTeX citekey) and a genre (a.k.a. Entry Types).

    .. note::

        We do restrict the allowed syntax for the id to make sure it can safely be used
        as path component in a URL. To skip this check, pass `_check_id=False` to the
        constructor.
    """

    def __init__(self, genre, id_, *args, **kw):
        if kw.pop('_check_id', True) and not ID_PATTERN.match(id_):
            raise ValueError(id_)
        self.genre = genre
        self.id = id_
        super(Source, self).__init__(*args, **kw)

    def __bool__(self):  # pragma: no cover
        return True

    __nonzero__ = __bool__

    def __str__(self):
        return self.text()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.id)

    @classmethod
    def from_entry(cls, key, entry):
        """
        Factory method to initialize a `Source` instance from a `pybtex.database.Entry`.

        :param key: Citation key, e.g. a key in `pybtex.database.BibliographyData.entries`.
        :param entry: `pybtex.database.Entry`
        """
        kw = {k: v for k, v in entry.fields.items()}
        for role in (entry.persons or []):
            if entry.persons[role]:
                kw[role] = ' and '.join('%s' % p for p in entry.persons[role])
        return cls(entry.type, key, **kw)

    @classmethod
    def from_bibtex(cls, bibtexString, lowercase=False, _check_id=True):
        source = None

        # the following patterns are designed to match preprocessed input lines.
        # i.e. the configuration values given in the bibtool resource file used to
        # generate the bib-file have to correspond to these patterns.

        # in particular, we assume all key-value-pairs to fit on one line,
        # because we don't want to deal with nested curly braces!
        lines = bibtexString.strip().split('\n')

        # genre and key are parsed from the @-line:
        atLine = re.compile("^@(?P<genre>[a-zA-Z_]+)\s*{\s*(?P<key>[^,]*)\s*,\s*")

        # since all key-value pairs fit on one line, it's easy to determine the
        # end of the value: right before the last closing brace!
        fieldLine = re.compile('\s*(?P<field>[a-zA-Z_]+)\s*=\s*(\{|")(?P<value>.+)')

        endLine = re.compile("}\s*")

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

    def bibtex(self):
        """Represent the source in BibTeX format.

        :return: string encoding the source in BibTeX syntax.
        """
        m = max(itertools.chain(map(len, self), [0]))
        fields = ("  %s = {%s}" % (k.ljust(m), self[k]) for k in self)
        return "@%s{%s,\n%s\n}" % (
            getattr(self.genre, 'value', self.genre), self.id, ",\n".join(fields))

    _genre_note = {
        'phdthesis': 'Doctoral dissertation',
        'mastersthesis': 'MA thesis',
        'unpublished': 'unpublished',
    }

    def get_with_translation(self, key):
        res = self.get(key)
        if res and self.get(key + '_english'):
            res = '{0} [{1}]'.format(res, self.get(key + '_english'))
        return res

    def text(self):
        """Linearize the bib source according to the rules of the unified style.

        Book:
        author. year. booktitle. (series, volume.) address: publisher.

        Article:
        author. year. title. journal volume(issue). pages.

        Incollection:
        author. year. title. In editor (ed.), booktitle, pages. address: publisher.

        .. seealso::

            http://celxj.org/downloads/UnifiedStyleSheet.pdf
            https://github.com/citation-style-language/styles/blob/master/\
            unified-style-linguistics.csl
        """
        genre = getattr(self.genre, 'value', self.genre)
        pages_at_end = genre in (
            'book',
            'phdthesis',
            'mastersthesis',
            'misc',
            'techreport')
        thesis = genre in ('phdthesis', 'mastersthesis')

        if self.get('editor'):
            editors = self['editor']
            affix = 'eds' if ' and ' in editors or '&' in editors else 'ed'
            editors = " %s (%s.)" % (editors, affix)
        else:
            editors = None

        res = [self.get('author', editors), self.get('year', 'n.d')]
        if genre == 'book':
            res.append(self.get_with_translation('booktitle') or
                       self.get_with_translation('title'))
            series = ', '.join(filter(None, [self.get('series'), self.get('volume')]))
            if series:
                res.append('(%s.)' % series)
        elif genre == 'misc':
            # in case of misc records, we use the note field in case a title is missing.
            res.append(self.get_with_translation('title') or self.get('note'))
        else:
            res.append(self.get_with_translation('title'))

        if genre == 'article':
            atom = ' '.join(filter(None, [self.get('journal'), self.get('volume')]))
            if self.get('issue'):
                atom += '(%s)' % self['issue']
            res.append(atom)
            res.append(self.get('pages'))
        elif genre == 'incollection' or genre == 'inproceedings':
            prefix = 'In'
            atom = ''
            if editors:
                atom += editors
            if self.get('booktitle'):
                if atom:
                    atom += ','
                atom += " %s" % self.get_with_translation('booktitle')
            if self.get('pages'):
                atom += ", %s" % self['pages']
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
                    res.append(self.get(attr))

            if self.get('issue'):
                res.append("(%s)" % self['issue'])

            if not pages_at_end and self.get('pages'):
                res.append(self['pages'])

        if self.get('publisher'):
            res.append(": ".join(filter(None, [self.get('address'), self['publisher']])))
        else:
            if genre == 'misc' and self.get('howpublished'):
                res.append(self.get('howpublished'))

        if not thesis and pages_at_end and self.get('pages'):
            res.append(self['pages'] + 'pp')

        note = self.get('note') or self._genre_note.get(genre)
        if note and note not in res:
            if thesis:
                joiner = ','
                if self.get('school'):
                    note += '{0} {1}'.format(joiner, self.get('school'))
                    joiner = ';'
                if self.get('pages'):
                    note += '{0} {1}pp.'.format(joiner, self.get('pages'))
            res.append('(%s)' % note)

        return ' '.join(
            x if x.endswith(('.', '.)')) else '%s.' % x for x in res if x)
