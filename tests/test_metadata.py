from clldutils.metadata import *


def test_roundtrip():
    md = Metadata(url='http://example.org')
    assert Metadata.from_jsonld(md.to_jsonld()) == md
    assert md.domain == 'example.org'


def test_defaults():
    md = Metadata.from_jsonld({}, defaults={'title': 'x', 'license.name': 'cc'})
    assert md.title == 'x'
    assert md.license.name == 'cc'


def test_license_lookup():
    lic = License(name='CC-BY-4.0')
    assert lic.url == 'https://creativecommons.org/licenses/by/4.0/'
