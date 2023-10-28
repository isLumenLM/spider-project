# -*- coding: utf-8 -*-
# @Time    : 2022/7/18 21:55
# @Author  : LM
import hashlib

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