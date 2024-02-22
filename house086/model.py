# -*- coding: utf-8 -*-
# @Time    : 2024/2/6 16:20
# @Author  : LiuMing
# @Email   : liuming04073@zulong.com
# @File    : model.py
from peewee import MySQLDatabase

import setting

db = MySQLDatabase(database='house086',
                   host=setting.host,
                   port=setting.port,
                   user=setting.user,
                   password=setting.password)