FROM mysql:5.7

ENV MYSQL_ROOT_PASSWORD=admin

VOLUME /var/lib/mysql

# 拉取镜像
# docker build -t mysql:5.7 .
# 拉取镜像后运行：
# docker run --name mysql -d -p 3306:3306 -v /var/lib/mysql:/var/lib/mysql mysql:5.7
# 运行命令行
# docker exec -it mysql /bin/bash
# 进入mysql后登录
# mysql -u root -p
# 创建database
# CREATE DATABASE tmjy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# set character_set_client=utf8mb4;
# set character_set_connection=utf8mb4;
# set character_set_database=utf8mb4;
# set character_set_results=utf8mb4;
# set character_set_server=utf8mb4;