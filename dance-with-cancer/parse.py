# -*- coding: utf-8 -*-
# @Time    : 2022/7/12 21:27
# @Author  : LM

from datetime import datetime
import re
from typing import List, Optional

import execjs
import peewee
import requests
from lxml import etree
from pybloom_live import ScalableBloomFilter

import sys

from requester import get
from selector import Selector
from model import PostInfo, ReplyInfo, UserInfo, UserPostHistory, UserReplyHistory, db, Url, Friends, Target
from utils import md5_url, check_url

delay = [1, 3]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

db.connect()

sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH, error_rate=0.000001)
if db.table_exists(Url):
    for i in Url.select():
        sbf.add(i.urlid)


def login(username: str, password: str, encryption: bool = False) -> requests.Session:
    """
    登陆函数
    :param username: 用户名
    :param password: 密码
    :param encryption: 是否对密码进行加密，密码不能明文
    :return: requests.Session
    """
    if encryption:
        import hashlib
        password = hashlib.md5(password.encode()).hexdigest()

    session = requests.Session()
    get_url = 'https://www.yuaigongwu.com/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
    response = get(url=get_url, headers=headers, session=session, time_delay=delay)

    html = etree.HTML(response.content)

    post_url = 'https://www.yuaigongwu.com/' + html.xpath('//*[@name="login"]/@action')[0]
    formhash = html.xpath('//*[@name="formhash"]/@value')[0]

    data = {
        'formhash': formhash,
        'referer': 'https://www.yuaigongwu.com/portal.php',
        'username': username,
        'password': password,
        'questionid': 0,
        'answer': ''
    }
    response = session.post(url=post_url, data=data, headers=headers)
    if response.status_code != 404:
        return session
    else:
        raise ConnectionError('登陆失败!')


session = login('isLumen', 'aa0beaa62b67748ebf5f6e86c7265c4d')


def _get_dsign(url: str) -> Optional[str]:
    """ js逆向 获取url中的dsign参数 """
    # url = 'https://www.yuaigongwu.com/forum.php?mod=viewthread&tid=98585'
    response = requests.get(url=url, headers=headers)
    root = etree.HTML(response.text)
    selector = Selector(root=root)

    script = selector.xpath('//script/text()').get()
    func = ('function get_dsign() {'
            'window = {};'
            'location = {'
            'assign: function(url) {location.href=url;},'
            'replace: function(url) {location.href=url;}'
            '};'
            + script
            + 'if (location.href != null) {'
              'return location.href;'
              '} else {'
              'return location;'
              '}'
              '}')
    # 试验后发现会返回一些本来就是错误的js
    # 导致这个函数报错，因此写个try
    try:
        get_dsign = execjs.compile(func)
        design = get_dsign.call('get_dsign').split('=')[1]
    except execjs._exceptions.ProcessExitedWithNonZeroStatus:
        return _get_dsign(url)
    except AttributeError:
        return None

    return design


def check_content(selector: Selector) -> bool:
    """ 检查帖子"""
    # 有无权限
    if selector.xpath('//*[@id="messagetext"]').get():
        return False

    # 是否禁止发言
    if selector.xpath('//div[@class="pbm mbm bbda cl"][last()]'
                      '/ul/li/em[starts-with(text(),"用户组")]/'
                      'following-sibling::span/a/text()').get() == '禁止发言':
        return False

    # 是否用户隐藏
    # https://www.yuaigongwu.com/home.php?mod=space&uid=77313&do=friend&from=space&page=1
    if selector.xpath('//h2[@class="xs2"]/text()').get():
        if selector.xpath('//h2[@class="xs2"]/text()').get().strip().startswith('抱歉'):
            return False

    if selector.xpath('//*[@id="messagetext"]/p/text()').get() == '抱歉，指定的主题不存在或已被删除或正在被审核':
        return False

    return True


def save_model(model: peewee.Model):
    """ 保存model 存到数据库 """
    try:
        ret = model.save(force_insert=True)
        if ret:
            print('数据保存成功')
        else:
            print('数据保存失败', ret)
    except Exception as e:
        print('数据保存失败', e)


def post_parse(pid: int, userinfo: bool = True):
    """ 帖子解析 """
    # https://www.yuaigongwu.com/thread-58219-1-1.html
    url = 'https://www.yuaigongwu.com/thread-{}-{}-1.html'
    design = _get_dsign(url.format(pid, 1))
    # design = ''
    if design:
        url += '?_dsign=' + design
    else:
        return

    au_add_time = []
    page = 0
    while True:
        page += 1
        # if not check_url(url.format(pid, page), sbf): continue
        response = get(url=url.format(pid, page), headers=headers, session=session, time_delay=delay)
        root = etree.HTML(response.text)
        selector = Selector(root=root)

        # 没权限 直接退出
        if not check_content(selector): return

        regx = '//*[@class="comiis_pgs cl"]/*[@class="pg"]/label/span/text()'
        total_page = selector.xpath(regx).get()
        if total_page:
            total_page = int(total_page.split()[1])
        else:
            total_page = 1
        if page > total_page:
            break

        # 帖子基本信息
        if page == 1:
            regx = '//*[@id="thread_subject"]/text()'
            title = selector.xpath(regx).get()

            regx = '//*[@id="comiis_authi_author_div"]/following-sibling::text()[1]'
            posttime = selector.xpath(regx).get()
            if posttime != '\n发表于 ':
                if posttime:
                    posttime = datetime.strptime(posttime.split('发表于 ')[1].strip(), '%Y-%m-%d %H:%M:%S')
                else:
                    page -= 1
                    continue
            else:
                regx = '//*[@id="comiis_authi_author_div"]/following-sibling::span[1]/@title'
                posttime = datetime.strptime(selector.xpath(regx).get(), '%Y-%m-%d %H:%M:%S')

            regx = '//*[@class="xg1"]/*[contains(@href, "space")]/@href'
            uid = selector.xpath(regx).get()
            if uid:
                uid = uid.split('uid=')[1]
            else:
                uid = '123456'

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "forum.php?gid=")]/@href'
            gid = selector.xpath(regx).get()
            if gid:
                gid = re.findall(re.compile(r'gid=(\d+)'), gid)[0]

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "forum.php?gid=")]/text()'
            gname = selector.xpath(regx).get()

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "forum.php?mod=forumdisplay&fid=")]/@href'
            fid = selector.xpath(regx).get()
            if fid:
                fid = re.findall(re.compile(r'fid=(\d+)'), fid)[0]

            regx = '//div[@id="pt"]/div[@class="z"]/a[starts-with(@href, "forum.php?mod=forumdisplay&fid=")]/text()'
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
                        ']/text()')
                posttext = ''.join([i.get().strip() for i in posttext[0].xpath(regx)])

            regx = '//*[@class="views"]/text()'
            views = selector.xpath(regx).get()

            regx = '//*[@class="replies"]/text()'
            replies = selector.xpath(regx).get()

            regx = '//*[@id="recommend_add"]/i/span/text()'
            support = selector.xpath(regx).get()

            regx = '//*[@id="recommend_subtract"]/i/span/text()'
            oppose = selector.xpath(regx).get()

            regx = '//span[@id="favoritenumber"]/text()'
            collect = selector.xpath(regx).get(default=0)

            regx = '//span[@id="sharenumber"]/text()'
            share = selector.xpath(regx).get(default=0)

            regx = '//*[@class="xg1"]/a[@c="1"]/text()'
            uname = selector.xpath(regx).get()
            if not uname:
                uname = '匿名'

            au_add_time.append(uname + ' 发表于 ' + posttime.strftime('%Y-%m-%d %H:%M'))

            user_parse(uid)
            if userinfo:
                history_post_parse(uid)
                history_reply_parse(uid)
                friends_parse(uid)

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

            # 楼主也算回帖
            regx = '//div[@class="comiis_vrx comiis_viewbox_nr"]/@id'
            rid = selector.xpath(regx).get()
            if rid:
                rid = rid.split('_')[1]
            reply = ReplyInfo(
                rid=rid,
                pid=pid,
                uid=uid,
                uname=uname,
                replytime=posttime,
                text=posttext,
                floor='1',
                url=url.format(pid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(reply)
            reply.print()

        # 回帖信息
        reply_div = selector.xpath('//*[@class="comiis_viewbox" or @class="comiis_viewbox tkmone"]')
        for i, r in enumerate(reply_div):
            if page == 1 and i == 0:
                continue

            regx = './/div[@class="comiis_vrx comiis_viewbox_nr"]/@id'
            rid = r.xpath(regx).get()
            if rid:
                rid = rid.split('_')[1]

            regx = './/*[@c="1"]/@href'
            uid = r.xpath(regx).get()
            if uid:
                uid = uid.split('uid=')[1]

            regx = './/*[contains(@id, "authorposton")]/text()'
            replytime = r.xpath(regx).get()
            if replytime != '发表于 ':
                replytime = datetime.strptime(replytime.split('发表于 ')[1], '%Y-%m-%d %H:%M:%S')
            else:
                regx = './/*[contains(@id, "authorposton")]/span/@title'
                replytime = datetime.strptime(r.xpath(regx).get(), '%Y-%m-%d %H:%M:%S')

            regx = './/*[contains(@id, "postmessage")]/text()'
            text = ''.join([i.get().strip() for i in r.xpath(regx)])

            floor_map = {
                '沙发': '2',
                '板凳': '3',
                '地板': '4',
            }
            regx = './/*[@class="pi"]/strong/a/text() | .//*[@class="pi"]/strong/a/em/text()'
            floor = ''.join([i.get().strip() for i in r.xpath(regx)])
            if floor in floor_map:
                floor = floor_map[floor]

            regx = './/*[@class="authi"]/a[@c="1"]/text()'
            uname = r.xpath(regx).get()
            if not uname:
                uname = '匿名'

            regx = './/div[@class="quote"]/blockquote/font/a/font/text()'
            quote = r.xpath(regx).get()
            if not quote:
                regx = './/div[@class="quote"]/blockquote/font/font/text()'
                quote = r.xpath(regx).get()
            father = None
            if quote:
                if '发表于' in quote:
                    n = quote.split('发表于')[0].strip()
                    try:
                        t = datetime.strptime(quote.split('发表于')[1].strip(), '%Y-%m-%d %H:%M').strftime(
                            '%Y-%m-%d %H:%M')
                    except ValueError:
                        t = quote.split('发表于')[1].strip()
                else:
                    n = quote.split()[0].strip()
                    try:
                        t = datetime.strptime(' '.join(quote.split()[1:]).strip(), '%Y-%m-%d %H:%M').strftime(
                            '%Y-%m-%d %H:%M')
                    except ValueError:
                        t = ''
                quote = n + ' 发表于 ' + t
                if quote in au_add_time:
                    father = au_add_time.index(quote) + 1

            au_add_time.append(uname + ' 发表于 ' + replytime.strftime('%Y-%m-%d %H:%M'))

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
        sbf.add(md5_url(url.format(pid, page)))


def user_parse(uid: str):
    """ 用户解析 """
    # https://www.yuaigongwu.com/home.php?mod=space&uid=76907&do=profile
    url = 'https://www.yuaigongwu.com/home.php?mod=space&uid={}&do=profile'

    if not check_url(url.format(uid), sbf): return
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

    regx = '//div[@id="psts"]/ul/li/em[starts-with(text(), "版块积分")]/parent::li/text()'
    sectionpoint = selector.xpath(regx).get()

    regx = '//div[@id="psts"]/ul/li/em[starts-with(text(), "与爱共舞币")]/parent::li/text()'
    coin = selector.xpath(regx).get()

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "好友数")]/text()'
    friends = selector.xpath(regx).get()
    if friends:
        friends = friends.split()[1]

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "主题数")]/text()'
    posts = selector.xpath(regx).get()
    if posts:
        posts = posts.split()[1]

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "回帖数")]/text()'
    replys = selector.xpath(regx).get()
    if replys:
        replys = replys.split()[1]

    regx = '//ul[@class="cl bbda pbm mbm"]/li/a[starts-with(text(), "分享数")]/text()'
    shares = selector.xpath(regx).get()
    if shares:
        shares = shares.split()[1]

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
        sectionpoint=sectionpoint,
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
    sbf.add(md5_url(url.format(uid)))


def history_post_parse(uid: str):
    """ 用户历史发帖 """
    url = 'https://www.yuaigongwu.com/home.php?mod=space&uid={}&do=thread&view=me&type=thread&order=dateline&from=space&page={}'
    page = 0
    while True:
        page += 1

        if not check_url(url.format(uid, page), sbf): continue
        response = get(url=url.format(uid, page), headers=headers, session=session, time_delay=delay)
        html = etree.HTML(response.text)
        selector = Selector(root=html)

        if not check_content(selector): break

        regx = '//p/text()'
        if selector.xpath(regx).get() == '还没有相关的帖子':
            break

        regx = '//div[@id="ct"]/div[@class="mn"]/div[@class="bm"]/div[@class="bm_c"]/div[@class="tl"]/form/table/tr[not(@class="th")]'
        th = selector.xpath(regx)
        for t in th:
            regx = './th/a/@href'
            post_url = t.xpath(regx).get()
            pid = re.findall(re.compile(r'tid=(\d+)'), post_url)[0]

            post_parse(pid, userinfo=False)

            history = UserPostHistory(
                uphid=uid + pid,
                uid=uid,
                pid=pid,
                post_url='https://www.yuaigongwu.com/' + post_url,
                url=url.format(uid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(history)
            history.print()

        urlmodel = Url(urlid=md5_url(url.format(uid, page)),
                       url=url.format(uid, page))
        save_model(urlmodel)


def history_reply_parse(uid: str):
    """ 用户历史回帖 """
    url = 'https://www.yuaigongwu.com/home.php?mod=space&uid={}&do=thread&view=me&type=reply&order=dateline&from=space&page={}'
    page = 0
    while True:
        page += 1

        if not check_url(url.format(uid, page), sbf): continue
        response = get(url=url.format(uid, page), headers=headers, session=session, time_delay=delay)
        html = etree.HTML(response.text)
        selector = Selector(root=html)

        if not check_content(selector): break

        regx = '//div[@class="tl"]/form/table/tr[not(@class="th")]/td/p/text()'
        if selector.xpath(regx).get() == '还没有相关的帖子':
            break

        regx = '//div[@id="ct"]/div[@class="mn"]/div[@class="bm"]/div[@class="bm_c"]/div[@class="tl"]/form/table/tr[not(@class="th")]'
        tr = selector.xpath(regx)
        pid = None
        for t in tr:
            is_post = t.xpath('./@class').get() == 'bw0_all'
            if is_post:
                regx = './th/a/@href'
                pid = t.xpath(regx).get()
                if pid:
                    pid = re.findall(re.compile(r'tid=(\d+)'), pid)[0]

                    post_parse(pid, userinfo=False)

            else:
                regx = './td/a/text()'
                text = t.xpath(regx).get()

                regx = './td/a/@href'
                replyurl = t.xpath(regx).get()
                rid = None
                if replyurl:
                    replyurl = 'https://www.yuaigongwu.com/' + replyurl

                    rid = replyurl.split('pid=')[1]

                history = UserReplyHistory(
                    urhid=uid + pid,
                    uid=uid,
                    pid=pid,
                    rid=rid,
                    text=text,
                    replyurl=replyurl,
                    url=url.format(uid, page),
                    spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                )

                save_model(history)
                history.print()

        urlmodel = Url(urlid=md5_url(url.format(uid, page)),
                       url=url.format(uid, page))
        save_model(urlmodel)
        sbf.add(md5_url(url.format(uid, page)))


def friends_parse(uid: str):
    """ 好友解析器 """
    # https://www.yuaigongwu.com/home.php?mod=space&uid=3&do=friend&from=space&page=1
    url = 'https://www.yuaigongwu.com/home.php?mod=space&uid={}&do=friend&from=space&page={}'
    page = 0
    while True:
        page += 1
        if not check_url(url.format(uid, page), sbf): continue
        response = get(url=url.format(uid, page), headers=headers, session=session, time_delay=delay)
        html = etree.HTML(response.text)
        selector = Selector(root=html)

        if not check_content(selector): break

        regx = '//div[@class="emp"]/text()'
        if selector.xpath(regx).get() == '没有相关成员':
            break

        regx = '//*[@class="bbda cl"]'
        li = selector.xpath(regx)
        for l in li:
            regx = './h4/a/@href'
            friendid = l.xpath(regx).get().split('uid=')[1]
            friendid = friendid

            user_parse(friendid)

            friends = Friends(
                id=uid + friendid,
                uid=uid,
                friendid=friendid,
                url=url.format(uid, page),
                spidertime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )

            save_model(friends)
            friends.print()

        urlmodel = Url(urlid=md5_url(url.format(uid, page)),
                       url=url.format(uid, page))
        save_model(urlmodel)
        sbf.add(md5_url(url.format(uid, page)))


def main():
    tables = [UserInfo, PostInfo, ReplyInfo, UserPostHistory, UserReplyHistory, Url, Friends]
    for table in tables:
        if not db.table_exists(table):
            db.create_tables([table])
    # with open('tid.txt', 'r') as f:
    #     for line in f.readlines():
    #         pid = int(line.strip())
    #
    #         post_parse(pid, True)
    idx = 0
    try:
        while True:
            post_parse(idx, False)
            idx += 1
    except Exception as e:
        print(e)
    finally:
        db.close()

    return True


if __name__ == '__main__':
    # while True:
    #     try:
    #         flag = main()
    #         if flag:
    #             break
    #     except:
    #         continue
    main()
    # while True:
    #     _get_dsign('1')

    # tables = [UserInfo, PostInfo, ReplyInfo, UserPostHistory, UserReplyHistory, Url, Friends]
    # for table in tables:
    #     if not db.table_exists(table):
    #         db.create_tables([table])
    # history_reply_parse('76907')
    # user_parse('93018')
    # firends_parse('3')
    # history_reply_parse('3')

    # resopnse = session.get('https://www.yuaigongwu.com/home.php?mod=space&uid=109382&do=thread&view=me&type=reply&order=dateline&from=space&page=10', headers=headers)
    # print(resopnse.text)

    # post_parse(111442, userinfo=True)

    # with open('tid.txt', 'r') as f:
    #     for line in f.readlines():
    #         pid = int(line.strip())
    #
    #         sql = 'select friends from postinfo a left join userinfo b on a.uid_id=b.uid where pid={}'.format(pid)
    #         cursor = db.cursor()
    #         cursor.execute(sql)
    #         data = cursor.fetchall()
    #         print(data)
    # post_parse(207, False)

    # if not db.table_exists(Target):
    #     db.create_tables([Target])
    # with open('tid.txt', 'r') as f:
    #     for line in f.readlines():
    #         pid = int(line.strip())
    #
    #         target = Target(pid=pid)
    #         save_model(target)
