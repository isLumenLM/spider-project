# -*- coding: utf-8 -*-
# @Time    : 2022/7/18 11:18
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : http.py
from typing import Dict, Optional, List
import time
import random

import requests
from requests.models import Request, Response


def get(url: str, headers: Dict, session: requests.Session = requests.Session(), time_delay: Optional[List[int]] = None, *args, **kwargs):
    if time_delay:
        if len(time_delay) == 2:
            time.sleep(random.uniform(time_delay[0], time_delay[1]))
        else:
            raise ValueError('time_delay must be like [1, 2]')
    print('正在请求url：', url)
    response = session.get(url=url, headers=headers, *args, **kwargs)
    return response


def post(url: str, headers: Dict, data: Dict, session: requests.Session = requests.Session(), time_delay: Optional[List[int]] = None, *args, **kwargs):
    if time_delay:
        if len(time_delay) == 2:
            time.sleep(random.uniform(time_delay[0], time_delay[1]))
        else:
            raise ValueError('time_delay must be like [1, 2]')
    response = session.post(url=url, headers=headers, data=data, *args, **kwargs)
    return response


Request = Request
Response = Response


class RequestProcessor:

    def __init__(self, request: Request, session: requests.Session = requests.Session()):
        self.request = request
        self.session = session

    def get(self, url: str, headers: Dict, *args, **kwargs):
        return get(url=url, headers=headers, session=self.session, *args, **kwargs)

    def post(self, url: str, headers: Dict, data: Dict, *args, **kwargs):
        return post(url=url, headers=headers, data=data, session=self.session, *args, **kwargs)
