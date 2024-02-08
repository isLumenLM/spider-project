# -*- coding: utf-8 -*-
# @Time    : 2022/7/16 14:39
# @Author  : LM

from pprint import pprint

from peewee import *
import setting
from base_ import PrintMixin

db = MySQLDatabase(database='dancewithcancer',
                   host=setting.host,
                   port=setting.port,
                   user=setting.user,
                   password=setting.password)


class UserInfo(Model, PrintMixin):
    uid = IntegerField(primary_key=True)
    uname = CharField()
    group = CharField(null=True)
    visits = IntegerField(null=True)
    registertime = DateTimeField(null=True)
    onlinetime = FloatField(null=True)
    lastlogin = DateTimeField(null=True)
    lastpost = DateTimeField(null=True)
    lastactive = DateTimeField(null=True)
    forumpoint = IntegerField(null=True)
    sectionpoint = IntegerField(null=True)
    coin = IntegerField(null=True)
    friends = IntegerField(null=True)
    posts = IntegerField(null=True)
    replys = IntegerField(null=True)
    shares = IntegerField(null=True)
    usedspace = CharField(null=True)
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class PostInfo(Model, PrintMixin):
    pid = IntegerField(primary_key=True)
    title = CharField()
    posttime = DateTimeField()
    uid = IntegerField()
    gid = IntegerField()
    gname = CharField()
    fid = IntegerField()
    fname = CharField()
    uname = CharField()
    posttext = TextField()
    views = IntegerField()
    replies = IntegerField()
    support = IntegerField()
    oppose = IntegerField()
    collect = IntegerField()
    share = IntegerField()
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class ReplyInfo(Model, PrintMixin):
    rid = IntegerField(primary_key=True)
    pid = IntegerField()
    uid = IntegerField()
    uname = CharField()
    replytime = DateTimeField()
    text = TextField()
    floor = CharField(max_length=30)
    father = IntegerField(null=True)
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class UserPostHistory(Model, PrintMixin):
    uphid = CharField(primary_key=True)
    uid = IntegerField()
    pid = IntegerField()
    post_url = CharField()
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class UserReplyHistory(Model, PrintMixin):
    urhid = CharField(primary_key=True)
    uid = IntegerField()
    pid = IntegerField()
    rid = IntegerField()
    text = TextField()
    replyurl = CharField()
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class Friends(Model, PrintMixin):
    id = CharField(primary_key=True)
    uid = IntegerField(UserInfo)
    friendid = IntegerField(UserInfo)
    url = CharField()
    spidertime = DateTimeField()

    class Meta:
        database = db


class Url(Model):
    urlid = CharField(primary_key=True)
    url = CharField()

    class Meta:
        database = db


class Target(Model):
    pid = IntegerField(primary_key=True)

    class Meta:
        database = db
