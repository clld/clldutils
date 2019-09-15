
def test_replace():
    from clldutils.lgr import replace

    for i, o in [
        ('1SG', '<first person singular>'),
        ('DUR.DU-', '<durative>.<dual>-'),
    ]:
        assert replace(i) == o

    assert replace('DUR.DU-', lambda m: m.group('pre') + '#') == '#.#-'
    assert replace('.XX-', custom={'XX': 'x'}) == '.<x>-'
