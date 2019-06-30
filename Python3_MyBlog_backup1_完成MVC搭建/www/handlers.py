#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

# 专注地往handlers模块不断添加URL处理函数了，可以极大地提高开发效率

__author__ = 'Toohoo Lee'

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post

from models import User, Comment, Blog, next_id

@get('/')
async def index(request):
    users = await User.findAll()
    # 将查询出来的结果：用户集和对应的模板返回
    return {
        '__template__': 'test.html',
        'users': users
    }





















