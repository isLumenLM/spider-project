# -*- coding: utf-8 -*-
# @Time    : 2024/2/22 11:03
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : model.py
from peewee import MySQLDatabase, Model, CharField, IntegerField, DateTimeField, TextField, FloatField

import setting
from base_ import PrintMixin

db = MySQLDatabase(database='tmjy',
                   host=setting.host,
                   port=setting.port,
                   user=setting.user,
                   password=setting.password,
                   charset='utf8mb4',
                   collation='utf8mb4_unicode_ci')


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
    pid = CharField(primary_key=True)
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
    pid = CharField()
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


class Url(Model):
    urlid = CharField(primary_key=True)
    url = CharField()

    class Meta:
        database = db


class SucceedPid(Model):
    pid = CharField(primary_key=True)

    class Meta:
        database = db


class FailedPid(Model):
    pid = CharField(primary_key=True)

    class Meta:
        database = db


class TargetPid(Model):
    pid = CharField(primary_key=True)

    class Meta:
        database = db


class FidInfo(Model):
    fid = IntegerField()

    class Meta:
        database = db
