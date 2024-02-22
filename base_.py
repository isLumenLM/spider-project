# -*- coding: utf-8 -*-
# @Time    : 2024/2/6 16:22
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : base_.py
from pprint import pprint


class PrintMixin:

    def print(self):
        pprint(self.__class__.__name__)
        pprint(vars(self).get('__data__'))