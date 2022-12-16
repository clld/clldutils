"""
Support for accessing data in a repository with some "known locations" via an `API` object.
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
    """
    An API base class to provide programmatic access to data in a git repository.

    :ivar pathlib.Path repos: Path of the (data) repository.

    Some repositories provide functionality to explore their data, implemented as Javascript
    app that can be browsed locally, from the filesystem. This scenario is supported as follows:

    - the app is assumed to "live" in the :meth:`API.appdir` sub-directory,
    - browsable at `<API.appdir>/index.html`,
    - with app data at :meth:`API.appdatadir`.

    Then, a function which recreates the app data can be decorated with :meth:`API.app_wrapper`
    to initialise the app data directory and open the app in a browser after the method has
    finished.

    .. code-block:: python

            @API.app_wrapper
            def f(args):
                import shutil
                shutil.copy(args.api.path('stuff'), args.api.appdatadir)

    """

    #: A light-weight way to specifiy a default repository location (without having to
    #: overwrite __init__)
    __repos_path__ = None
    __default_metadata__ = None

    def __init__(self, repos=None):
        self.repos = pathlib.Path(repos or self.__repos_path__)

    def __str__(self):
        name = self.repos.resolve().name if self.repos.exists() else self.repos.name
        return '<{0} repository {1} at {2}>'.format(
            name, git_describe(self.repos), self.repos)

    def path(self, *comps: str) -> pathlib.Path:
        """
        A path within the repository.

        :param comps: path components relative to `self.repos`.
        """
        return self.repos.joinpath(*comps)

    @lazyproperty
    def dataset_metadata(self) -> Metadata:
        """
        If a repository provides metadata about the dataset curated there as JSON-LD file called
        `metadata.json`, this property returns a :class:`clldutils.metadata.Metadata` object,
        loaded from this metadata.
        """
        mdp = self.repos / 'metadata.json'
        return Metadata.from_jsonld(
            load(mdp) if mdp.exists() else {}, defaults=self.__default_metadata__)

    def assert_release(self):
        return assert_release(self.repos)

    @property
    def appdir(self) -> pathlib.Path:
        return self.path('app')

    @property
    def appdatadir(self) -> pathlib.Path:
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
