# -*- coding: utf-8 -*-
# @Time    : 2022/7/17 18:18
# @Author  : LM

from peewee import *

from peewee import *
import setting

import sys
sys.path.append(r'E:\Anaconda\envs\spider\Lib\site-packages\urllib3')
print(sys.path)
from urllib3.exceptions import HTTPError

db = MySQLDatabase(database='dancewithcancer',
                   host=setting.host,
                   port=setting.port,
                   user=setting.user,
                   password=setting.password)

class Person(Model):
    name = CharField()
    date = DateTimeField()
    i = IntegerField()

    class Meta:
        database = db

db.connect()
if not db.table_exists(Person):
    db.create_tables([Person])



Person(name='1111', date='2022-06-14', i="125312").save()
