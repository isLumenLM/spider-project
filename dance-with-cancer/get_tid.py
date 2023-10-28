# -*- coding: utf-8 -*-
# @Time    : 2022/7/21 22:03
# @Author  : LM
import pandas as pd
import re

data = pd.read_excel(r'D:\Project\PythonProject\spider-projects\dance-with-cancer\与癌共舞板块.xlsx')
pattern = r'(tid=(\d+) )| (thread-(\d+)-)'
for url in data['网址链接']:
    pattern = r'tid=(\d+)'
    tid = re.findall(re.compile(pattern), url)
    if not tid:
        pattern = r'thread-(\d+)-'
        tid = re.findall(re.compile(pattern), url)
    print(tid[0])
