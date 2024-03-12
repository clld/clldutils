import pytest
from markdown import markdown

from clldutils.source import Source


def test_checks():
    with pytest.raises(ValueError):
        Source('genre', 'a.b')

    assert Source('genre', 'a.b', _check_id=False).id == 'a.b'
    assert Source.from_bibtex('@misc{a.b,\n}', _check_id=False).id == 'a.b'


def test_lowercase():
    src = Source('Genre', 'a', _lowercase=True, Title='t')
    assert src.genre == 'genre' and src['title'] == 't'


def test_striptex():
    src = Source('Genre', 'a', _strip_tex=['title'], Title=r"{T}\'{a}ta")
    assert src['Title'] == 'Táta'


@pytest.mark.parametrize(
    'bib,txt',
    [
        (
            """@book{d_Anonimo_Geral,
  author    = {Anônimo},
  title     = {O diccionario anonymo da Lingua Geral do Brasil, publicado de novo com seu reverso por Julio Platzmann},
  publisher = {Leipzig: B.G. Teubner},
  address   = {Leipzig},
  pages     = {181},
  year      = {1896 [1795]}
}""",
            "Anônimo. 1896 [1795]. O diccionario anonymo da Lingua Geral do Brasil, publicado de novo com seu "
            "reverso por Julio Platzmann. Leipzig: B.G. Teubner. 181pp."),
        (
            """@book{314538,
  address   = {Pucallpa},
  author    = {Thiesen, Wesley},
  edition   = {2},
  publisher = {Ministerio de Educación and Instituto Lingüístico de Verano},
  series    = {Serie Lingüística Peruana},
  title     = {Gramática del idioma bora},
  volume    = {38},
  year      = {2008}
}""",
            "Thiesen, Wesley. 2008. Gramática del idioma bora. (Serie Lingüística Peruana, 38.) "
            "2nd edn. Pucallpa: Ministerio de Educación and Instituto Lingüístico de Verano."),
        (
                """@book{Dayley-1985,
  address    = {Berkeley},
  author     = {Dayley, Jon P.},
  iso_code   = {tzt; tzj},
  olac_field = {general_linguistics; semantics; morphology; typology; syntax},
  publisher  = {University of California Press},
  series     = {University of California Publications in Linguistics},
  title      = {Tzutujil Grammar},
  volume     = {107},
  wals_code  = {tzu},
  year       = {1985}
}""",
                "Dayley, Jon P. 1985. Tzutujil Grammar. (University of California "
                "Publications in Linguistics, 107.) Berkeley: University of California "
                "Press."),
        (
                """@misc{318762,
  author = {Cook, Eung-Do},
  editor = {Some One},
  title  = {A Tsilhqút'ín Grammar},
  issue  = {1},
  note   = {note},
  year   = {2013}
}""",
                "Cook, Eung-Do. 2013. A Tsilhq\xfat'\xedn Grammar. In  Some One (ed.) "
                "(1). (note)."),
        (
                """@article{467661,
  address   = {Berlin, New York},
  author    = {Al-Hazemi, Hassan},
  journal   = {IRAL - International Review of Applied Linguistics in Language Teaching},
  number    = {2},
  issue     = {1},
  pages     = {89-94},
  publisher = {Walter de Gruyter},
  title     = {Listening to the Yes/No vocabulary test},
  volume    = {38},
  year      = {2000},
  doi       = {10.1515/iral.2000.38.2.89},
  issn      = {0019-042X}
}""",
                "Al-Hazemi, Hassan. 2000. Listening to the Yes/No vocabulary test. IRAL "
                "- International Review of Applied Linguistics in Language Teaching "
                "38(1). 89-94. doi: 10.1515/iral.2000.38.2.89. Berlin, New York: "
                "Walter de Gruyter."),
        (
                """@book{318762,
  address   = {Vancouver},
  author    = {Cook, Eung-Do},
  pages     = {670},
  publisher = {UBC Press},
  series    = {First Nations Languages Series},
  title     = {A Tsilhqút'ín Grammar},
  year      = {2013}
}""",
                "Cook, Eung-Do. 2013. A Tsilhqút'ín Grammar. (First Nations Languages "
                "Series.) Vancouver: UBC Press. 670pp."),
        (
                """@inbook{316361,
  author    = {Healey, Alan},
  booktitle = {New Guinea area languages and language study},
  pages     = {223-232},
  title     = {History of research in Austronesian languages: Admiralty Islands area},
  volume    = {2}
}""",
                "Healey, Alan. n.d. History of research in Austronesian languages: "
                "Admiralty Islands area. 2. 223-232."),
        (
                """@incollection{316361,
  author    = {Healey, Alan},
  editor    = {Peter, Peter},
  booktitle = {New Guinea area languages and language study},
  pages     = {223-232},
  title     = {History of research in Austronesian languages: Admiralty Islands area},
  volume    = {2}
}""",
                "Healey, Alan. n.d. History of research in Austronesian languages: "
                "Admiralty Islands area. In Peter, Peter (ed.), "
                "New Guinea area languages and language study, 223-232."),
        (
                """@inproceedings{moisikesling2011,
  author    = {Moisik, Scott R. and Esling, John H.},
  booktitle = {Proceedings of the Congress of Phonetic Sciences (ICPhS XVII)},
  pages     = {1406-1409},
  title     = {The 'whole larynx' approach to laryngeal features},
  year      = {2011}
}""",
                "Moisik, Scott R. & John H. Esling. 2011. The 'whole larynx' approach "
                "to laryngeal features. In Proceedings of the Congress of "
                "Phonetic Sciences (ICPhS XVII), 1406-1409."),
        (
                """@mastersthesis{116989,
  address   = {Ann Arbor},
  author    = {Bryant, Michael G.},
  pages     = {ix+151},
  publisher = {UMI},
  school    = {University of Texas at Arlington},
  title     = {Aspects of Tirmaga Grammar},
  year      = {1999}
}""",
                "Bryant, Michael G. 1999. Aspects of Tirmaga Grammar. Ann Arbor: "
                "University of Texas at Arlington MA thesis. (ix+151pp.)"),
        (
                """@misc{316754,
  author       = {Radu Voica},
  howpublished = {Paper Presented at the APLL-6 Conference, SOAS, London},
  title        = {Towards and internal classification of the Isabel languages: Th},
  year         = {2013}
}""",
                "Voica, Radu. 2013. Towards and internal classification of the Isabel "
                "languages: Th. Paper Presented at the APLL-6 Conference, SOAS, London."),
        # Franks, Steven. 2005. Bulgarian clitics are positioned in the syntax.
        # http://www.cogs.indiana.edu/people/homepages/franks/Bg_clitics_remark_dense.pdf
        # (17 May, 2006.)
        (
                """@book{312817,
  address       = {Dar es Salaam},
  author        = {Rugemalira, Josephat Muhozi},
  pages         = {196},
  publisher     = {Mradi wa Lugha za Tanzania},
  title         = {Cigogo: kamusi ya Kigogo-Kiswahili-Kiingereza},
  year          = {2009},
  title_english = {Gogo-Swahili-English, English-Gogo}
}""",
                "Rugemalira, Josephat Muhozi. 2009. Cigogo: kamusi ya "
                "Kigogo-Kiswahili-Kiingereza [Gogo-Swahili-English, "
                "English-Gogo]. Dar es Salaam: Mradi wa Lugha za Tanzania. 196pp."),
        (
                """@book{lsp106,
  editor    = {Rehm, Georg and Stein, Daniel and Sasaki, Felix and Witt, Andreas},
  title     = {Language technologies for a multilingual Europe},
  year      = {2016},
  series    = {Translation and Multilingual Natural Language Processing},
  number    = {5},
  address   = {Berlin},
  publisher = {Language Science Press},
  doi       = {10.5281/zenodo.1291947}
}
""",
            "Rehm, Georg, Daniel Stein, Felix Sasaki & Andreas Witt (eds.) 2016. "
            "Language technologies for a multilingual Europe. "
            "(Translation and Multilingual Natural Language Processing, 5.) "
            "Berlin: Language Science Press. doi: 10.5281/zenodo.1291947."
        ),
        (
            """@phdthesis{116989,
  address = {Cambridge, MA},
  author  = {Author, T.},
  school  = {MIT},
  title   = {The Title},
  year    = {1999}
}""",
                "Author, T. 1999. The Title. Cambridge, MA: MIT dissertation."
        ),
        (
                """@phdthesis{116989,
  address = {Cambridge, MA},
  author  = {Author, T.},
  title   = {The Title},
  pages   = {250},
  year    = {1999}
}""",
                "Author, T. 1999. The Title. (dissertation, 250pp.)"
        ),
        (  # Example from the Unified stylesheet:
            """@phdthesis{1,
  address = {Berkeley, CA},
  author  = {Yu, Alan C. L.},
  school  = {University of California},
  title   = {The morphology and phonology of infixation},
  year    = {2003}
}""",
            "Yu, Alan C. L. 2003. The morphology and phonology of infixation. Berkeley, CA: "
            "University of California dissertation."
        ),
        (  # Article without pages:
            """@article{tarpent1983morphophonemics,
  title     = {Morphophonemics of Nisgha plural formation: A step towards},
  author    = {Tarpent, Marie-Lucie},
  year      = {1983},
  journal   = {Kansas Working Papers in Linguistics},
  publisher = {University of Kansas. Linguistics Graduate Student Association},
  volume    = {8},
  number    = {2}
}""",
            "Tarpent, Marie-Lucie. 1983. Morphophonemics of Nisgha plural formation: A step "
            "towards. Kansas Working Papers in Linguistics 8(2). University of Kansas. "
            "Linguistics Graduate Student Association."
        )
    ]
)
def test_linearization(bib, txt):
    rec = Source.from_bibtex(bib, lowercase=True)
    assert rec.text() == txt
    assert rec.bibtex().strip() == bib.strip()


@pytest.mark.parametrize(
    'genre,md,substring',
    [
        (
            'article',
            dict(author='A B', title='The title', journal='Journal', year='2002', pages='1-5'),
            '<em>Journal</em>'),
        (
            'article',
            dict(author='A B', title='T', journal='J', doi='x/y', year='2002', pages='1-5'),
            'href="https://doi.org/x/y"'),
        (
            'book',
            dict(author='A B', title='The title', address='place', year='2002', publisher='x'),
            '<em>The title</em>'),
    ]
)
def test_markdown(genre, md, substring):
    rec = Source(genre, '1', **md)
    res = markdown(rec.text(markdown=True))
    assert substring in res


def test_Source_from_entry(mocker):
    src = Source.from_entry(
        'xyz', mocker.Mock(type='misc', fields={'title': 'abc'}, persons=None))
    assert src.id == 'xyz'
    assert src.genre == 'misc'
    assert 'author' not in src
    assert src['title'] == 'abc'
    assert '{0}'.format(src) == 'n.d. abc.'
    assert repr(src) == '<Source xyz>'

    src = Source.from_entry(
        'xyz',
        mocker.Mock(
            type='misc',
            fields={'title': 'abc'},
            persons={'author': [r'Alfred E. N\'eumann', 'T. M.']}),
        _strip_tex=['author'])
    assert src['author'] == 'Alfred E. Néumann and T. M.'


def test_Source_split_names():
    assert len(Source.split_names('Name,')) == 1


@pytest.mark.parametrize(
    'names,res',
    [
        ('Kyle Johnson and Mark Baker and Ian Roberts', 'Johnson, Kyle, Mark Baker & Ian Roberts'),
        ('Stewart, Jr., Thomas W.', 'Stewart, Thomas W., Jr.'),
        ('Frans van Coetsem', 'Coetsem, Frans van'),
        ('Thomas Meier & Thomas Müller', 'Meier, Thomas & Thomas Müller'),
        ('', ''),
        ('Anonymous', 'Anonymous'),
    ]
)
def test_Source_reformat_names(names, res):
    assert Source.reformat_names(names) == res