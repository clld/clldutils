from clldutils.licenses import find


def test_find():
    assert find('http://creativecommons.org/licenses/by/4.0').id == 'CC-BY-4.0'
    assert find('CC-BY-4.0').url == 'https://creativecommons.org/licenses/by/4.0/'


def test_legalcode():
    assert find('cc-by-4.0').legalcode
    assert find('Zlib').legalcode is None
