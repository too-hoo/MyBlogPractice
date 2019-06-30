#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

'''
Models for user, blog, comment
'''

__author__ = 'Toohoo lee'

import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

# 主键id的缺省值是函数next_id，创建时间created_at的缺省值是函数time.time，可以自动设置当前日期和时间。
# 生成唯一的标识符号
def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):
    __table__ = 'users'

    # ddl表示数据定义的语言
    # 后面的id，email等会被实例的id，email覆盖
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)

















