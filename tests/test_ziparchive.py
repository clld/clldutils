
def test_ZipArchive(tmp_path):
    from clldutils.ziparchive import ZipArchive

    fname, text, name = tmp_path / 'test.zip', 'äöüß', 'test'

    with ZipArchive(fname, mode='w') as archive:
        archive.write_text(text, name)

    with ZipArchive(fname) as archive:
        assert text == archive.read_text(name)
