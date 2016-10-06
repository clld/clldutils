# coding: utf8
from __future__ import unicode_literals, print_function, division
import re

from tabulate import tabulate


class Table(list):
    def __init__(self, *cols, **kw):
        self.columns = list(cols)
        list.__init__(self, kw.pop('rows', []))

    def render(self, sortkey=None, condensed=True, verbose=False, reverse=False, **kw):
        """
        :param sortkey: A callable which can be used as key when sorting the rows.
        :param condensed: Flag signalling whether whitespace padding should be collapsed.
        :param verbose: Flag signalling whether to output additional info.
        :param reverse: Flag signalling whether we should sort in reverse order.
        :param kw: Additional keyword arguments are passed to the `tabulate` function.
        :return: String representation of the table in the chosen format.
        """
        tab_kw = dict(tablefmt='pipe', headers=self.columns, floatfmt='.2f')
        tab_kw.update(kw)
        res = tabulate(
            sorted(self, key=sortkey, reverse=reverse) if sortkey else self, **tab_kw)
        if tab_kw['tablefmt'] == 'pipe':
            if condensed:
                # remove whitespace padding around column content:
                res = re.sub('\|[ ]+', '| ', res)
                res = re.sub('[ ]+\|', ' |', res)
            if verbose:
                res += '\n\n(%s rows)\n\n' % len(self)
        return res
