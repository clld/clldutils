# coding: utf8
from __future__ import unicode_literals, print_function, division

from clldutils.misc import UnicodeMixin
from clldutils.path import git_describe, Path


#
# Functionality for simpler creation of models using the attrs library
#
def valid_enum_member(choices, instance, attribute, value):
    if value not in choices:
        raise ValueError(value)


def valid_range(min_, max_, instance, attribute, value):
    if value < min_ or value > max_:
        raise ValueError(value)


class API(UnicodeMixin):
    """
    An API base class to provide programmatic access to data in a git repository.
    """
    # A light-weight way to specifiy a default repository location (without having to
    # overwrite __init__)
    __repos_path__ = None

    def __init__(self, repos=None):
        self.repos = Path(repos or self.__repos_path__)

    def __unicode__(self):
        name = self.repos.resolve().name if self.repos.exists() else self.repos.name
        return '<{0} repository {1} at {2}>'.format(
            name, git_describe(self.repos), self.repos)

    def path(self, *comps):
        return self.repos.joinpath(*comps)
