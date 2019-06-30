#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

import orm
import asyncio
from models import User, Blog, Comment

# 必须写一个测试的类才行，不能直接写
async def test(loop):
    await orm.create_pool(loop, user='toohoo', password='123', db='myblogdb')
    # 创建实例：
    user = User(name='Bob', email='bob@example.com', passwd='1234567890', image='about:blank')
    # 存入数据库：
    # 必须使用await关键字，变成一个协程不能够直接使用user.save
    await user.save()
    # 查询所有的User对象：
    # await User.findAll()


# 加载test测试方法, 不用迭代的方法：for x in test(): pass
loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
print('test')
print('success')

# loop.close() # 关闭循环会出错





