"""
A minimalistic implementation of an OAI-PMH harvester.
"""
from typing import Union, Optional
import datetime
import collections
from collections.abc import Generator
import dataclasses
import urllib.parse
import urllib.request
from xml.etree import ElementTree

from ._compat import fromisoformat


__all__ = ['NAMESPACES', 'qname', 'Record', 'iter_records']

NAMESPACES = {
    'oai': "http://www.openarchives.org/OAI/2.0/",
    'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/",
    'dc': "http://purl.org/dc/elements/1.1/",
}


def qname(lname: str, prefix: str = 'oai') -> str:
    """
    Returns a qualified name suitable for use with ElementTree's namespace-aware functionality,
    see https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
    """
    return f'{{{NAMESPACES[prefix]}}}{lname}'


@dataclasses.dataclass
class Record:
    """
    :ivar identifier: the unique identifier of an item in a repository.
    :ivar oai_dc_metadata: `None` if no `oai_dc` metadata is available, otherwise a `dict` mapping \
    Dublin Core terms (specified as local names) to lists of values.
    """
    identifier: str
    datestamp: Union[datetime.datetime, str]
    metadata: Optional[ElementTree.Element] = None
    about: list = dataclasses.field(default_factory=list)
    sets: list = dataclasses.field(default_factory=list)
    status: Optional[str] = None
    oai_dc_metadata: Optional[dict] = None

    def __post_init__(self):
        self.datestamp = fromisoformat(self.datestamp)

    @classmethod
    def from_element(cls, e) -> 'Record':
        """Parse Record data from xml element."""
        header = e.find(qname('header'))
        md = e.find(qname('metadata'))
        status = header.attrib.get('status')
        oai_dc_metadata = None
        # Note: Deleted items may not have metadata!
        if status != 'deleted':
            ee = md.find(qname('dc', prefix='oai_dc'))
            if ee is not None:
                oai_dc_metadata = collections.defaultdict(list)
                for eee in ee.iter():
                    if eee.tag.startswith(qname('', prefix='dc')):
                        oai_dc_metadata[eee.tag.partition('}')[2]].append(eee.text)

        return cls(
            identifier=header.find(qname('identifier')).text,
            datestamp=header.find(qname('datestamp')).text,
            metadata=md,
            status=status,
            about=e.findall(qname('about')),
            sets=[ee.text for ee in header.findall(qname('setSpec'))],
            oai_dc_metadata=oai_dc_metadata
        )


class Response:  # pylint: disable=too-few-public-methods
    """An OAI-PMH response."""
    def __init__(self, xml):
        self.xml: ElementTree.Element = ElementTree.fromstring(xml)
        rt = self.xml.find(f".//{qname('resumptionToken')}")
        if isinstance(rt, ElementTree.Element):
            self.resumption_token: Optional[str] = rt.text
        else:
            self.resumption_token = None


def request(url: str, params: dict) -> Response:
    """Add params as query to url and request it."""
    parsed_url = list(urllib.parse.urlparse(url))
    parsed_url[4] = urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.parse.urlunparse(parsed_url)) as req:
        return Response(req.read().decode('utf8'))


def iter_records(
        baseURL: str,  # pylint: disable=invalid-name
        metadataPrefix: str = 'oai_dc',  # pylint: disable=invalid-name
        from_: Optional[Union[str, datetime.date, datetime.datetime]] = None,
        until: Optional[Union[str, datetime.date, datetime.datetime]] = None,
        set_: Optional[str] = None,
) -> Generator[Record, None, None]:
    """
    Runs a `ListRecords` request on the specified OAI-PMH repository (using resumption tokens as
    necessary).

    .. seealso:: `<https://www.openarchives.org/OAI/openarchivesprotocol.html#ListRecords>`_

    .. code-block:: python

        >>> from clldutils.oaipmh import iter_records
        >>> recs = iter_records('https://account.lddjournal.org/index.php/uv1-j-ldd/oai')
        >>> next(recs).identifier
        'oai:ojs.pkp.sfu.ca:article/2'
        >>> next(recs).oai_dc_metadata['identifier']
        ['https://account.lddjournal.org/index.php/uv1-j-ldd/article/view/12', '10.25894/ldd12']

    :param baseURL: the base URL of the repository
    :param metadataPrefix: specifies the metadataPrefix of the format that should be included in \
    the metadata part of the returned records.
    :param from: an optional argument with a UTCdatetime value, which specifies a lower bound for \
    datestamp-based selective harvesting.
    :param until: an optional argument with a UTCdatetime value, which specifies a upper bound for \
    datestamp-based selective harvesting.
    :param set_: an optional argument with a setSpec value , which specifies set criteria for \
    selective harvesting.
    """
    def format_date(d):
        if isinstance(d, str):
            return d
        return d.isoformat()

    params = {'verb': 'ListRecords', 'metadataPrefix': metadataPrefix}
    if from_:
        params['from'] = format_date(from_)
    if until:
        params['until'] = format_date(until)
    if set_:
        params['set'] = set_
    res = request(baseURL, params)
    while res:
        for e in res.xml.findall(f".//{qname('record')}"):
            yield Record.from_element(e)
        res = request(baseURL, {'verb': 'ListRecords', 'resumptionToken': res.resumption_token}) \
            if res.resumption_token else None
