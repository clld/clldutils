# coding: utf8
from __future__ import unicode_literals, print_function, division
import unittest


class Tests(unittest.TestCase):
    def test_checks(self):
        from clldutils.source import Source

        with self.assertRaises(ValueError):
            Source('genre', 'a.b')

        self.assertEqual(Source('genre', 'a.b', _check_id=False).id, 'a.b')
        self.assertEqual(Source.from_bibtex('@misc{a.b,\n}', _check_id=False).id, 'a.b')

    def test_linearization(self):
        from clldutils.source import Source

        for bib, txt in [
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
}
                """,
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
}
                """,
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
                "38(1). 89-94. Berlin, New York: Walter de Gruyter."),
            (
                """@book{318762,
  address   = {Vancouver},
  author    = {Cook, Eung-Do},
  pages     = {670},
  publisher = {UBC Press},
  series    = {First Nations Languages Series},
  title     = {A Tsilhqút'ín Grammar},
  year      = {2013}
}
                """,
                "Cook, Eung-Do. 2013. A Tsilhqút'ín Grammar. (First Nations Languages "
                "Series.) Vancouver: UBC Press. 670pp."),
            (
                """@inbook{316361,
  author    = {Healey, Alan},
  booktitle = {New Guinea area languages and language study},
  pages     = {223-232},
  title     = {History of research in Austronesian languages: Admiralty Islands area},
  volume    = {2}
}
                """,
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
}
                """,
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
                "Moisik, Scott R. and Esling, John H. 2011. The 'whole larynx' approach "
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
                "Bryant, Michael G. 1999. Aspects of Tirmaga Grammar. Ann Arbor: UMI. "
                "(MA thesis, University of Texas at Arlington; ix+151pp.)"),
            (
                """@misc{316754,
  author       = {Radu Voica},
  howpublished = {Paper Presented at the APLL-6 Conference, SOAS, London},
  title        = {Towards and internal classification of the Isabel languages: Th},
  year         = {2013}
}""",
                "Radu Voica. 2013. Towards and internal classification of the Isabel "
                "languages: Th. Paper Presented at the APLL-6 Conference, SOAS, London."),
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
        ]:
            rec = Source.from_bibtex(bib, lowercase=True)
            self.assertEqual(rec.text(), txt)
            self.assertEqual(rec.bibtex().strip(), bib.strip())
