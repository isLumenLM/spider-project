# -*- coding: utf-8 -*-
# @Time    : 2022/7/18 21:55
# @Author  : LM
import hashlib

import six
from pybloom_live import ScalableBloomFilter


def md5_url(url: str) -> str:
    md5 = hashlib.md5()
    md5.update(url.encode('utf-8'))
    return md5.hexdigest()


def check_url(url: str, sbf: ScalableBloomFilter) -> bool:
    url = md5_url(url)
    if url not in sbf:
        return True
    else:
        return False

def iflatten(x):
    """iflatten(sequence) -> Iterator
    Similar to ``.flatten()``, but returns iterator instead"""
    for el in x:
        if _is_listlike(el):
            for el_ in flatten(el):
                yield el_
        else:
            yield el

def _is_listlike(x):
    """
    >>> _is_listlike("foo")
    False
    >>> _is_listlike(5)
    False
    >>> _is_listlike(b"foo")
    False
    >>> _is_listlike([b"foo"])
    True
    >>> _is_listlike((b"foo",))
    True
    >>> _is_listlike({})
    True
    >>> _is_listlike(set())
    True
    >>> _is_listlike((x for x in range(3)))
    True
    >>> _is_listlike(six.moves.xrange(5))
    True
    """
    return hasattr(x, "__iter__") and not isinstance(x, (six.text_type, bytes))

def flatten(x):
    """flatten(sequence) -> list
    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).
    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    >>> flatten(["foo", "bar"])
    ['foo', 'bar']
    >>> flatten(["foo", ["baz", 42], "bar"])
    ['foo', 'baz', 42, 'bar']
    """
    return list(iflatten(x))