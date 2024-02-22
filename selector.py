# -*- coding: utf-8 -*-
# @Time    : 2022/7/16 15:03
# @Author  : LM
from typing import Optional, List

import six
from lxml import etree
from lxml.etree import _Element

from utils import iflatten


class Selector:

    def __init__(self, text: str = None, root: _Element = None):
        if text:
            root = self._get_root(text)
        elif root is None:
            raise ValueError("Selector needs either text or root argument")

        self.root = root
        self.selector_ls = SelectorList

    def _get_root(self, text: str) -> _Element:
        return etree.HTML(text)

    def xpath(self, query: str):
        return self.selector_ls([self.__class__(root=i) for i in self.root.xpath(query)])

    def get(self):
        try:
            return etree.tostring(self.root,
                                  method='html',
                                  encoding='unicode',
                                  with_tail=False)
        except (AttributeError, TypeError):
            if self.root is True:
                return u'1'
            elif self.root is False:
                return u'0'
            else:
                return six.text_type(self.root)


class SelectorList(list):

    def __getitem__(self, pos):
        o = super(SelectorList, self).__getitem__(pos)
        return self.__class__(o) if isinstance(pos, slice) else o

    def xpath(self, xpath: str):
        return self.__class__(self.__flatten([x.xpath(xpath) for x in self]))

    def get(self, index: int = 0, default=None) -> Optional[Selector]:
        try:
            return self[index].get()
        except IndexError:
            return default

    def get_all(self) -> List:
        return [self[i].get() for i in range(len(self))]

    @staticmethod
    def __flatten(x):
        return list(iflatten(x))


if __name__ == '__main__':
    MyStr = '''<meta name="baidu-site-verification" content="cZdR4xxR7RxmM4zE" />
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="Sun, 6 Mar 2005 01:00:00 GMT">
        '''
    selector = Selector(text=MyStr)
    print(selector.xpath('//meta').get(4))
