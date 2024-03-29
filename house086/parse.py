# -*- coding: utf-8 -*-
# @Time    : 2024/2/6 16:11
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : parse.py
import re
from datetime import datetime

import requests
from lxml import etree
from pybloom_live import ScalableBloomFilter

from house086.model import db, Url, SucceedPid, PostInfo, ReplyInfo, UserInfo, FailedPid
from requester import get
from selector import Selector
from utils import check_url, md5_url, save_model

delay = [1, 3]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

db.connect()

url_sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH, error_rate=0.000001)
if db.table_exists(Url):
    for i in Url.select():
        url_sbf.add(i.urlid)

pid_sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH, error_rate=0.000001)
if db.table_exists(SucceedPid):
    for i in SucceedPid.select():
        pid_sbf.add(i.pid)


def check_content(selector: Selector) -> bool:
    """ 检查帖子"""
    if selector.xpath('//*[@id="messagetext"]/p/text()').get() == '抱歉，指定的主题不存在或已被删除或正在被审核':
        return False

        # 有无权限
    if selector.xpath('//*[@id="messagetext"]').get():
        return False

    # 是否禁止发言
    if selector.xpath('//div[@class="pbm mbm bbda cl"][last()]'
                      '/ul/li/em[starts-with(text(),"用户组")]/'
                      'following-sibling::span/a/text()').get() == '禁止发言':
        return False

    # 是否用户隐藏
    if selector.xpath('//h2[@class="xs2"]/text()').get():
        if selector.xpath('//h2[@class="xs2"]/text()').get().strip().startswith('抱歉'):
            return False

    return True


session = requests.Session()


def post_parse(pid: int):
    if pid in pid_sbf:
        return

    url = 'https://www.house086.com/thread-{}-{}-1.html'
    page = 0
    au_add_time = {}
    while True:
        page += 1
        # 检查帖子是否爬过
        if not check_url(url.format(pid, page), url_sbf):
            continue

        response = get(url=url.format(pid, page), headers=headers, session=session, time_delay=delay)
        root = etree.HTML(response.text)
        selector = Selector(root=root)

        # 检查帖子是否有异常
        if not check_content(selector):
            urlmodel = Url(urlid=md5_url(url.format(pid, page)),
                           url=url.format(pid, page))
            save_model(urlmodel)
            url_sbf.add(md5_url(url.format(pid, page)))
            return

        # 获取总共页码
        regx = '//div[@class="pgs mtm mbm cl"]/div[@class="pg"]/label/span/text()'
        total_page = selector.xpath(regx).get()
        if total_page:
            total_page = int(total_page.split(' ')[2])
        else:
            total_page = 1
        if page > total_page:
            break

        # 帖子基本信息
        if page == 1:
            regx = '//span[@id="thread_subject"]/text()'
            title = selector.xpath(regx).get()

            regx = '//div[@class="pti"]/div[@class="authi"]/em/text()'
            posttime = selector.xpath(regx).get()
            posttime = datetime.strptime(posttime.split('发表于')[1].strip(), '%Y-%m-%d %H:%M:%S')

            regx = '//div[@id="postlist"]/div[starts-with(@id, "post_")][1]//td[@class="pls"]/div/div/div/a[@class="xw1"]/@href'
            uid = selector.xpath(regx).get()
            uid = uid.split("-")[-1].split('.')[0]

            regx = '//div[@id="postlist"]/div[starts-with(@id, "post_")][1]//td[@class="pls"]/div/div/div/a[@class="xw1"]/text()'
            uname = selector.xpath(regx).get()

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum.php?gid=")]/@href'
            gid = selector.xpath(regx).get()
            if gid:
                gid = re.findall(re.compile(r'gid=(\d+)'), gid)[0]

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum.php?gid=")]/text()'
            gname = selector.xpath(regx).get()

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum.php?mod=forumdisplay&fid=")]/@href'
            fid = selector.xpath(regx).get()
            if fid:
                fid = re.findall(re.compile(r'fid=(\d+)'), fid)[0]
            else:
                regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum-")]/@href'
                fid = selector.xpath(regx).get()
                if fid:
                    fid = fid.split('-')[1]

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum.php?mod=forumdisplay&fid=")]/text()'
            fname = selector.xpath(regx).get()
            if not fname:
                regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "https://www.house086.com/forum-")]/text()'
                fname = selector.xpath(regx).get()

            regx = '//*[contains(@id,"postmessage")]'
            posttext = selector.xpath(regx)
            if posttext:
                regx = ('./descendant-or-self::*[not(@class="xg1 y") '
                        'and not(@class="xg1") '
                        'and not(@class="jammer")'
                        'and not(@class="mag_viewthread")'
                        'and not(@style="display:none")'
                        'and not(contains(text(), "下载附件"))'
                        'and not(starts-with(text(), "image"))'
                        'and not(@type="text/javascript") '
                        ']/text()')
                posttext = ''.join([i.get().strip() for i in posttext[0].xpath(regx)])

            regx = '//div[@class="hm ptn"]/span[@class="xi1"][1]/text()'
            views = selector.xpath(regx).get()

            regx = '//div[@class="hm ptn"]/span[@class="xi1"][2]/text()'
            replies = selector.xpath(regx).get()

            regx = '//*[@id="recommend_add"]/i/span/text()'
            support = selector.xpath(regx).get()

            regx = '//*[@id="recommend_subtract"]/i/span/text()'
            oppose = selector.xpath(regx).get()

            regx = '//span[@id="favoritenumber"]/text()'
            collect = selector.xpath(regx).get(default=0)

            regx = '//span[@id="sharenumber"]/text()'
            share = selector.xpath(regx).get(default=0)

            au_add_time[uname + ' 发表于 ' + posttime.strftime('%Y-%m-%d %H:%M').replace('-0', '-')] = '1'

            user_parse(uid)

            post = PostInfo(
                pid=pid,
                title=title,
                posttime=posttime.strftime('%Y-%m-%d %H:%M:%S'),
                uid=uid,
                gid=gid,
                gname=gname,
                fid=fid,
                fname=fname,
                uname=uname,
                posttext=posttext,
                views=views,
                replies=replies,
                support=support,
                oppose=oppose,
                collect=collect,
                share=share,
                url=url.format(pid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(post)
            post.print()

            regx = '//div[@id="postlist"]/div[starts-with(@id, "post_")][1]/@id'
            rid = selector.xpath(regx).get()
            if rid:
                rid = rid.split('_')[1]
            reply = ReplyInfo(
                rid=rid,
                pid=pid,
                uid=uid,
                uname=uname,
                replytime=posttime.strftime('%Y-%m-%d %H:%M:%S'),
                text=posttext,
                floor='1',
                url=url.format(pid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(reply)
            reply.print()

            # 回帖
        reply_div = selector.xpath('//div[@id="postlist"]/div[starts-with(@id, "post_")]')
        for i, r in enumerate(reply_div):
            if page == 1 and i == 0:
                continue

            regx = './/td[@class="plc"]/div[@class="pi"]/strong/a/em/text()'
            floor = r.xpath(regx).get()
            if not floor:
                continue

            regx = './/@id'
            rid = r.xpath(regx).get()
            if rid:
                rid = rid.split('_')[1]

            regx = './/td[@class="pls"]/div/div/div/a[@class="xw1"]/@href'
            uid = r.xpath(regx).get()
            if uid:
                uid = uid.split("-")[-1].split('.')[0]
            else:
                continue

            regx = './/td[@class="pls"]/div/div/div/a[@class="xw1"]/text()'
            uname = r.xpath(regx).get()

            regx = './/*[contains(@id, "authorposton")]/text()'
            replytime = r.xpath(regx).get()
            if replytime != '发表于 ':
                replytime = datetime.strptime(replytime.split('发表于 ')[1], '%Y-%m-%d %H:%M:%S')
            else:
                regx = './/*[contains(@id, "authorposton")]/span/@title'
                replytime = datetime.strptime(r.xpath(regx).get(), '%Y-%m-%d %H:%M:%S')

            regx = './/*[contains(@id, "postmessage")]/text()'
            text = ''.join([i.get().strip() for i in r.xpath(regx)])

            regx = './/div[@class="quote"]/blockquote/font/text()'
            quote = r.xpath(regx).get()
            father = None
            if quote:
                father = au_add_time.get(quote, None)

            au_add_time[uname + ' 发表于 ' + replytime.strftime('%Y-%m-%d %H:%M').replace('-0', '-')] = floor

            user_parse(uid)

            reply = ReplyInfo(
                rid=rid,
                pid=pid,
                uid=uid,
                uname=uname,
                replytime=replytime.strftime('%Y-%m-%d %H:%M:%S'),
                text=text,
                floor=floor,
                father=father,
                url=url.format(pid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(reply)
            reply.print()

        urlmodel = Url(urlid=md5_url(url.format(pid, page)),
                       url=url.format(pid, page))
        save_model(urlmodel)
        url_sbf.add(md5_url(url.format(pid, page)))


def user_parse(uid: str):
    url = 'https://www.house086.com/home.php?mod=space&uid={}&do=profile'

    if not check_url(url.format(uid), url_sbf): return
    response = get(url=url.format(uid), headers=headers, session=session, time_delay=delay)
    html = etree.HTML(response.text)
    selector = Selector(root=html)

    regx = '//title/text()'
    uname = selector.xpath(regx).get()
    if uname:
        uname = uname.split('的个人资料')[0]

    regx = '//div[@class="pbm mbm bbda cl"][last()]/ul/li/em[starts-with(text(),"用户组")]/following-sibling::span/a/text()'
    group = selector.xpath(regx).get()

    regx = '//ul[@class="pf_l cl pbm mbm"]/li/em[starts-with(text(),"空间访问量")]/following-sibling::strong/text()'
    visits = selector.xpath(regx).get()

    regx = '//ul[@id="pbbs"]/li/em[starts-with(text(), "注册时间")]/parent::li/text()'
    registertime = selector.xpath(regx).get()

    regx = '//ul[@id="pbbs"]/li/em[starts-with(text(), "在线时间")]/parent::li/text()'
    onlinetime = selector.xpath(regx).get()
    if onlinetime:
        onlinetime = onlinetime.split()[0]
    else:
        onlinetime = ''

    regx = '//ul[@id="pbbs"]/li/em[starts-with(text(), "最后访问")]/parent::li/text()'
    lastlogin = selector.xpath(regx).get()

    regx = '//ul[@id="pbbs"]/li/em[starts-with(text(), "上次发表时间")]/parent::li/text()'
    lastpost = selector.xpath(regx).get()

    regx = '//ul[@id="pbbs"]/li/em[starts-with(text(), "上次活动时间")]/parent::li/text()'
    lastactive = selector.xpath(regx).get()

    regx = '//div[@id="psts"]/ul/li/em[starts-with(text(), "积分")]/parent::li/text()'
    forumpoint = selector.xpath(regx).get()

    regx = '//div[@id="psts"]/ul/li/em[starts-with(text(), "家园豆")]/parent::li/text()'
    coin = selector.xpath(regx).get()

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "好友数")]/text()'
    friends = selector.xpath(regx).get()
    if friends:
        friends = friends.split()
        if len(friends) > 1:
            friends = friends[1]
        else:
            friends = 0

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "主题数")]/text()'
    posts = selector.xpath(regx).get()
    if posts:
        posts = posts.split()
        if len(posts) > 1:
            posts = posts[1]
        else:
            posts = 0

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "回帖数")]/text()'
    replys = selector.xpath(regx).get()
    if replys:
        replys = replys.split()
        if len(replys) > 1:
            replys = replys[1]
        else:
            replys = 0

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "分享数")]/text()'
    shares = selector.xpath(regx).get()
    if shares:
        shares = shares.split()
        if len(shares) > 1:
            shares = shares[1]
        else:
            shares = 0

    regx = '//div[@id="psts"]/ul/li/em[starts-with(text(), "已用空间")]/parent::li/text()'
    usedspace = selector.xpath(regx).get()

    user = UserInfo(
        uid=uid,
        uname=uname,
        group=group,
        visits=visits,
        registertime=registertime,
        onlinetime=onlinetime,
        lastlogin=lastlogin,
        lastpost=lastpost,
        lastactive=lastactive,
        forumpoint=forumpoint,
        coin=coin,
        friends=friends,
        posts=posts,
        replys=replys,
        shares=shares,
        usedspace=usedspace,
        url=url.format(uid),
        spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )

    save_model(user)
    user.print()

    urlmodel = Url(urlid=md5_url(url.format(uid)),
                   url=url.format(uid))
    save_model(urlmodel)
    url_sbf.add(md5_url(url.format(uid)))


def main():
    tables = [UserInfo, PostInfo, ReplyInfo, Url, SucceedPid, FailedPid]
    for table in tables:
        if not db.table_exists(table):
            db.create_tables([table])
    idx = 0
    while True:
        try:
            post_parse(idx)
            succeed_pid = SucceedPid(pid=idx)
            save_model(succeed_pid)
        except Exception as e:
            failed_pid = FailedPid(pid=idx)
            save_model(failed_pid)
        finally:
            idx += 1


if __name__ == '__main__':
    main()
