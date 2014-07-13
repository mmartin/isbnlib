# -*- coding: utf-8 -*-
"""Hyphenate an ISBN."""

import logging
from ._data.data4mask import ranges
from ._core import canonical, to_isbn13, EAN13

LOGGER = logging.getLogger(__name__)


def msk(isbn, separator='-'):
    """Transform a canonical ISBN to a `masked` one.

    `Mask` the ISBN, separating by identifier
    ISBN-10 identifiers: country-publisher-title-check

    Used the iterative version of the `sliding-window` algorithm.
    Not pretty but fast! Lines 36-46 implement the search loop.
    O(n) for n - number of keys, if data structure like ranges in data4mask.py
    """
    ib = canonical(isbn)
    ean = EAN13(ib)
    if len(ib) not in (10, 13) or ean is None:
        LOGGER.warning('%s is not a valid ISBN', isbn)
        return

    isbn10 = False
    if len(ib) == 10:
        check10 = ib[-1]
        ib = to_isbn13(ib)
        isbn10 = True

    idx = None
    check = ib[-1:]                     # <-- hack!
    cur = 3
    igi = cur
    buf = ib[igi:cur + 1]
    group = ib[0:cur] + '-' + buf

    for _ in range(6):
        if group in ranges:
            sevens = ib[cur + 1:cur + 8].ljust(7, '0')
            for l in ranges[group]:
                if l[0] <= int(sevens) <= l[1]:
                    idx = l[2]
                    break
            break
        cur += 1
        buf = ib[igi:cur + 1]
        group = group + buf[-1:]        # <-- hack!

    if idx:
        if isbn10:
            group = group[4:]
            check = check10
        return separator.join([group, ib[cur + 1:cur + idx + 1],
                              ib[cur + idx + 1:-1], check])
    LOGGER.warning('identifier not found! Please, update the program.')  # pragma: no cover
    return                                                               # pragma: no cover
