#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

__author__ = 'Toohoo lee'

'''
async web application.
'''

import logging;logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime
from aiohttp import web

# 加入注册支持, FileSystemLoader 是文件系统加载器， 用来加载模板路径
from jinja2 import Environment, FileSystemLoader

import orm
from coroweb import add_routes, add_static


def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        # 自动转义xml/html的特殊字符
        autoescape = kw.get('autoescape', True),
        # 代码块的开始结束标志
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        # 变量的开始结束标志
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        # 当模板文件被修改之后，下次请求加载该模板文件的时候就会自动重新加载修改后的模板文件
        auto_reload = kw.get('auto_reload', True)
    )
    # 获取模板文件的位置
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    # Environment是jinja2中的一个核心类，它的实例用来保存配置，全局对象和模板文件的路径
    env = Environment(loader=FileSystemLoader(path), **options)
    # filters: 一个字典描述的filter过滤器集合， 如果非模板被加载的时候,可以安全的添加或者较早的移除。
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    # 所有的一切是为了给app添加__templating__字段
    # 前面将jinja2的环境配置都赋值给了env了，这里再把env存入app的dict中，这样app就知道要到哪里去找模板，怎样解析模板。
    app['__templating__'] = env

# 中间件可以改变URL的输入、输出，甚至可以决定不继续处理而直接返回。middleware的用处就是在于把通用的功能从每个URL处理函数中拿出来，
# 集中放到一个地方。
# 这个函数的作用就是当有http请求的时候，通过logging.info 输出请求的信息，其中包括请求的路径和方法
async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0.3)
        # handler 为处理函数，request为参数
        return (await handler(request))
    return logger


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    # 返回函数parse_data
    return parse_data


# 请求对象request的处理工序流水线先后依次是：
#     logger_factory->response_factory->RequestHandler().__call__->get或post->handler
# 对应的响应的对象response的处理工序流水线先后依次是：
# 由handler构造出要返回的具体对象
# 然后在这个返回的对象上加上‘__method__’和‘__route__’属性，以标识别这个对象并使得接下来的程序容易处理
# RequestHandler目的就是从请求的对象request的请求content中获取必要的参数，调用URL处理函数，然后把结果返回给response_factory
# response_factory在拿到经过处理的对象，经过一系列类型判断，构造出正确的web.Response对象，以正确的方式返回给客户端
# 在这个过程中，只关心handler的处理其他的都走统一的通道，如果需要差异化处理，就在通道中选择合适的地方添加处理代码。
# 注意：在response_factory中应用了jinja2来渲染模板文件
async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        # 大多数返回的是dict
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                # 对模板进行渲染
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


def datetime_filter(t):
    delta =int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


# 更新使用async实现
async def init(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='toohoo', password='123', db='myblogdb')
    # middleware（中间件）设置3个中间处理函数（都是装饰器）
    # middleware中的每个factory接受两个参数，app和handler（即middleware的下一个handler）
    # 例如这里的logger_factory的handler参数其实就是auth_factory
    # middlewares 的最后一个元素的handler会通过routes查找到相应的，就是routes注册的对应handler处理函数
    # 这里是装饰模式的体现，logger_factory, auth_factory, response_factory都是URL处理函数前（如handler.index）的装饰功能
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters = dict(datetime=datetime_filter))
    # 添加URL处理函数
    add_routes(app, 'handlers')
    # 添加CSS等静态文件路径
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)

    logging.info('server started at http://127.0.0.1:9000...')
    return srv

# 获取eventloop
loop = asyncio.get_event_loop()
# 然后加入运行事件
loop.run_until_complete(init(loop))
loop.run_forever()











# 更新
# routes = web.RouteTableDef()
#
# @routes.get('/')
# async def index(request):
#     await asyncio.sleep(2)
#     # 需要添加content_type='text/html'，按照html的格式解析
#     return web.Response(text="<h1>Index Awesome</h1>",content_type='text/html')
#
#
# @routes.get('/about')
# async def about(request):
#     await asyncio.sleep(0.5)
#     return web.json_response({
#         'name':'about us'
#     })
#
# def init():
#     # 初始化
#     app = web.Application()
#     app.add_routes(routes)
#     # logging.info('server started at http://127.0.0.1:8080...')
#     web.run_app(app)
#
# init()
