"""
Support for accessing data in a repository with some "known locations".
"""
import re
import json
import pathlib
import functools
import webbrowser

import attr

from clldutils.misc import lazyproperty
from clldutils.path import git_describe
from clldutils.attrlib import valid_range
from clldutils.metadata import Metadata
from clldutils.jsonlib import load

VERSION_NUMBER_PATTERN = re.compile(
    r'v(?P<number>(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9]+))?)$')


#
# Common attributes of data objects
#
def latitude():
    return attr.ib(
        converter=lambda s: None if s is None or s == '' else float(s),
        validator=valid_range(-90, 90, nullable=True))


def longitude():
    return attr.ib(
        converter=lambda s: None if s is None or s == '' else float(s),
        validator=valid_range(-180, 180, nullable=True))


def value_ascsv(v):
    if v is None:
        return ''
    elif isinstance(v, float):
        return "{0:.5f}".format(v)
    elif isinstance(v, dict):
        return json.dumps(v)
    elif isinstance(v, list):
        return ';'.join(v)
    return "{0}".format(v)


@attr.s
class DataObject(object):

    @classmethod
    def fieldnames(cls):
        return [f.name for f in attr.fields(cls)]

    def ascsv(self):
        res = []
        for f, v in zip(attr.fields(self.__class__), attr.astuple(self)):
            res.append((f.metadata.get('ascsv') or value_ascsv)(v))
        return res


def assert_release(repos):
    match = VERSION_NUMBER_PATTERN.match(git_describe(repos))
    assert match, 'Repository is not checked out to a valid release tag'
    return match.group('number')  # pragma: no cover


class API(object):
    """An API base class to provide programmatic access to data in a git repository."""

    # A light-weight way to specifiy a default repository location (without having to
    # overwrite __init__)
    __repos_path__ = None
    __default_metadata__ = None

    def __init__(self, repos=None):
        self.repos = pathlib.Path(repos or self.__repos_path__)

    def __str__(self):
        name = self.repos.resolve().name if self.repos.exists() else self.repos.name
        return '<{0} repository {1} at {2}>'.format(
            name, git_describe(self.repos), self.repos)

    def path(self, *comps):
        return self.repos.joinpath(*comps)

    @lazyproperty
    def dataset_metadata(self):
        mdp = self.repos / 'metadata.json'
        return Metadata.from_jsonld(
            load(mdp) if mdp.exists() else {}, defaults=self.__default_metadata__)

    @property
    def appdir(self):
        return self.path('app')

    @property
    def appdatadir(self):
        return self.appdir.joinpath('data')

    @classmethod
    def app_wrapper(cls, func):
        @functools.wraps(func)
        def wrapper(args):
            if isinstance(args.repos, cls):
                api = args.repos
            else:
                api = cls(args.repos)
            if (not api.appdatadir.exists()) \
                    or getattr(args, 'recreate', False) \
                    or getattr(args, 'force', False) \
                    or (hasattr(args, 'args') and '--recreate' in args.args):
                api.appdatadir.mkdir(exist_ok=True)
                args.api = api
                func(args)
            index = api.appdir / 'index.html'
            if index.exists():
                webbrowser.open(index.resolve().as_uri())
        return wrapper

    def assert_release(self):
        return assert_release(self.repos)
