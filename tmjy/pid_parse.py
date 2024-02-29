# -*- coding: utf-8 -*-
# @Time    : 2024/2/29 14:17
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : pid_parse.py
import re

import requests
from lxml import etree
from pybloom_live import ScalableBloomFilter

import sys
sys.path.append('..')

from requester import get
from selector import Selector
from tmjy.model import db, FidInfo, TargetPid, Url
from utils import save_model, md5_url, check_url

delay = [1, 2]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

db.connect()

session = requests.Session()

sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH, error_rate=0.000001)


def get_fid():
    url = 'https://bbs.tnbz.com/'
    response = get(url=url, headers=headers, session=session)
    html = etree.HTML(response.text)
    selector = Selector(root=html)

    regx = '//*[contains(@href, "fid=")]/@href'
    fid_ls = selector.xpath(regx).get_all()
    if not fid_ls:
        regx = '//*[starts-with(@href, "https://bbs.tnbz.com/forum-")]/@href'
        fid_ls = selector.xpath(regx).get_all()
        fid_ls = list(map(lambda x: x.split('-')[1], fid_ls))
    else:
        fid_ls = list(map(lambda x: re.findall(re.compile(r'fid=(\d+)'), x)[0], fid_ls))

    fid_ls = sorted([int(i) for i in set(fid_ls)])
    sub_fid_ls = []

    for fid in fid_ls:
        save_model(FidInfo(fid=fid))
        url = 'https://bbs.tnbz.com/forum.php?mod=forumdisplay&fid={}'.format(fid)
        response = get(url=url, headers=headers, session=session, time_delay=delay)
        html = etree.HTML(response.text)
        selector = Selector(root=html)

        regx = '//div[@class="bm bmw fl"]'
        sub_forum = selector.xpath(regx).get()
        if sub_forum:
            regx = '//div[@class="bm bmw fl"]//td[@class="fl_icn"]/a/@href'
            sub_fids = selector.xpath(regx).get_all()
            if sub_fids:
                if 'fid' in sub_fids[0]:
                    sub_fids = list(map(lambda x: re.findall(re.compile(r'fid=(\d+)'), x)[0], sub_fids))
                else:
                    sub_fids = list(map(lambda x: x.split('-')[1], sub_fids))
            sub_fids = sorted([int(i) for i in set(sub_fids)])
            sub_fid_ls.extend(sub_fids)

            for sub_fid in sub_fids:
                save_model(FidInfo(fid=sub_fid))

    return sorted(fid_ls)


def get_pid(fid: int):
    page = 0
    while True:
        page += 1
        url = 'https://bbs.tnbz.com/forum.php?mod=forumdisplay&fid={}&page={}'.format(fid, page)

        if not check_url(url, sbf):
            continue

        response = get(url=url, headers=headers, session=session, time_delay=delay)
        html = etree.HTML(response.text)
        selector = Selector(root=html)

        # 获取总共页码
        regx = '//span[@id="fd_page_bottom"]/div[@class="pg"]/label/span/@title'
        total_page = selector.xpath(regx).get()
        if total_page:
            total_page = int(total_page.split(' ')[1])
            print(total_page)
        else:
            total_page = 1
        if page > total_page:
            break

        regx = '//tbody[starts-with(@id, "normalthread_")]/@id'
        pid_ls = selector.xpath(regx).get_all()
        pid_ls = list(map(lambda x: x.split('_')[1], pid_ls))
        for pid in pid_ls:
            save_model(TargetPid(pid=pid))
        sbf.add(md5_url(url))
        urlmodel = Url(urlid=md5_url(url),
                       url=url)
        save_model(urlmodel)


def main():
    if not db.table_exists(FidInfo):
        db.create_tables([FidInfo])
        get_fid()

    if not db.table_exists(TargetPid):
        db.create_tables([TargetPid])
    for fid in FidInfo.select():
        if fid.fid != 1:
            get_pid(fid.fid)


if __name__ == '__main__':
    main()
