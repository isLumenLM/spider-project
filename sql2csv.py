# -*- coding: utf-8 -*-
# @Time    : 2023/11/2 20:58
# @Author  : Lumen
# @File    : sql2csv.py


import pymysql
import pandas as pd
import argparse

import setting

# 解析命令行参数
parser = argparse.ArgumentParser(description='Script to export MySQL table to CSV file.')
parser.add_argument('-d', '--database', required=True, help='Name of the database to export.')
parser.add_argument('-t', '--table', required=True, help='Name of the table to export.')
parser.add_argument('-f', '--fileout', required=True, help='Path to save CSV file.')
args = parser.parse_args()

# Prompt for database credentials
hostname = setting.host
username = setting.user
password = setting.password
database = args.database

# 建立数据库连接
conn = pymysql.connect(
    host=hostname,
    user=username,
    passwd=password,
    db=database,
    charset='utf8mb4'
)

try:
    # 查询表
    query = f'SELECT * FROM {args.table}'

    # 使用pandas的read_sql_query函数读取查询结果
    df = pd.read_sql_query(query, conn)

    # 将DataFrame保存为CSV文件
    df.to_csv(args.fileout, index=False, encoding='utf-8')

    print(f'Table {args.table} has been saved to {args.fileout}')

finally:
    # 关闭数据库连接
    conn.close()