#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

# 专注地往handlers模块不断添加URL处理函数了，可以极大地提高开发效率

__author__ = 'Toohoo Lee'

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post

from models import User, Comment, Blog, next_id

import markdown2
from aiohttp import web
from apis import APIValueError, APIResourceNotFoundError, APIError, APIPermissionError, Page

from models import User, Comment, Blog, next_id
from config import configs

COOKIE_NAME = 'myblogsession'
_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(r'^[0-9a-z\.\_\-]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# 获取当前页页码, 供下面调用
def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


# 计算加密cookie：
def user2cookie(user, max_age):
    """
    Generate cookie str by user(id-expires-sha1).
    """
    # build cookie string by: id-expires-sha1
    # 过期时间是创建是时间+存活时间
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    # sha1是一种单向算法，可以通过原始字符串计算出SHA1结果，但无法通过SHA1结果反推出原始字符串。
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

def text2html(text):
    # HTML 转义字符
    # “             &quot;
    # &             &amp;
    # <             &lt;
    # >             &gt;
    # 不断开空格     &nbsp
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '%amp;').replace('<', '&alt;').replace('>', '&gt;'),
                filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


# 解密cookie
async def cookie2user(cookie_str):
    """
    Parse cookie and load user if cookie is valid.
    """
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/')
async def index(*, page='1'):
    # summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    # blogs = [
    #     Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
    #     Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
    #     Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
    # ]
    page_index = get_page_index(page)
    # 查找博客表里面的条目数
    num = await Blog.findNumber('count(id)')
    # 没有条目则不显示
    if not num or num == 0:
        logging.info('the type of num is :%s' % type(num))
        blogs = []
    else:
        page = Page(num, page_index)
        # 根据计算出来的offset（取到的初始条目数index）和limit（取到的条数），来取出条目
        # 首页只是显示5篇文章
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))

    # 将查询出来的结果：用户集和对应的模板返回
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
        # '__template__' 指定的模板文件是blogs.html, 其他参数是传递给模板的数据
    }

@post('/result')
async def handler_url_result(*, user_email, request):
    response = '<h1>你输入的邮箱是%s</h1>' % user_email
    return response




@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]

    # 在Python 3.x 版本中，把‘xxx’和u'xxx'统一成Unicode编码，即写不写前缀u都是一样的，
    # 而以字节形式表示的字符串则必须加上b前缀：b'xxx'.
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')


    # 检查密码
    # browser_sha1_passwd = '%s:%s' % (user.id, passwd)
    # browser_sha1 = hashlib.sha1(browser_sha1_passwd.encode('utf-8'))
    # if user.passwd != browser_sha1.hexdigest():
    #     raise APIValueError('passwd', 'Invalid password')

    # authenticate ok, set cookie
    # 验证成功通过之后，设置cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = "******"
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
def signout(request):
    # 1.从请求头获取Referer信息
    referer = request.headers.get('Referer')
    # 赋值给r
    r = web.HTTPFound(referer or '/')
    # 清理掉cookie来退出账户
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r




# -------------------------------管理用户---------------------------------------------
# 用户列表页面，未测试
@get('/manage/users')
def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }

# 获取用户，获取后端数据库的数据API
@get('/api/users')
async def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    # count是MySQL中的聚集函数，用于计算某列的行数
    # user_count 代表有多少个用户id
    user_count = await User.findNumber('count(id)')
    p = Page(user_count, page_index)
    # 通过Page类来计算当前页的相关信息，其实是数据库limit语句中的offset, limit
    if user_count == 0:
        return dict(page=p, users=())
    # page.offset表示从哪一行开始检索，page.limit表示检索多少行
    users = await User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))

    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


# 注册/创建新的用户
@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    # 该邮箱是否已经注册
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')

    uid = next_id()
    # 数据库中存储的passwd是经过SHA1计算后的40位Hash字符串，所以服务器端并不知道用户的原始口令。
    # 使用用户uid和原始密码拼接成新密码
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    # 保存用户
    await user.save()

    # make session cookie:产生session和cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 显示所有用户
@get('/show_all_users')
async def show_all_users():
    users = await User.findAll()
    logging.info('to index...')
    return {
        '__template__': 'all_users.html',
        'users': users
    }


# -------------------------------管理博客---------------------------------------------
# 获取到博客并转成HTML
@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    # text直接转成HTML
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        "blog": blog,
        'comments': comments
    }


@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }


# 创建博客，无需参数
@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'  # 对应HTML页面中VUE的actions名字
    }

# 后台提供博客信息
@get('/api/blogs')
async def api_blogs(*, page='1'):
    # 获取页面首页
    page_index = get_page_index(page)
    # 获取总的博客数目
    blogs_count = await Blog.findNumber('count(id)')
    # 对博客进行分页
    p = Page(blogs_count, page_index)
    if blogs_count == 0:
        return dict(page=p, blogs=())
    # 分页完成之后将博客查询出来
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


# 请求具体的某条博客：插入某条博客之后马上调用这个方法回显
@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog


# 创建某条博客
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    # 判断是否是管理员
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image,
                name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    # 返回一个dict， 没有模板， 会把信息直接显示出来
    return blog


# 修改博客
@post('/api/blogs/modify')
async def api_modify_blog(request, *, id, name, summary, content):
    logging.info('修改的博客的ID为：%s' % id)

    check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')

    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()

    await blog.update()
    return blog


# 管理修改博客，需要传入参数id
@get('/manage/blogs/modify/{id}')
def manage_modify_blog(*, id):
    return {
        '__template__': 'manage_blog_modify.html',
        'id': id,
        'action': '/api/blogs/modify'
    }


# 删除博客
@post('/api/blogs/{id}/delete')
async def api_delete_blog(id, request):
    logging.info('删除博客的ID为：%s' % id)
    # 先要检查是否有权限
    check_admin(request)
    b = await Blog.find(id)
    if b is None:
        raise APIResourceNotFoundError('Blog')
    await b.remove()
    return dict(id=id)




# -------------------------------管理评论----------------------------------------------
@get('/manage/')
async def manage():
    # 当请求manage的时候，重定向到评论
    return 'redirect:/manage/comments'


# 管理评论
@get('/manage/comments')
async def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

@get('/api/comments')
async def api_comments(*, page='1'):
    # 获取起始页码
    page_index = get_page_index(page)
    # 查询出来有多少条评论
    num = await Comment.findNumber('count(id)')
    # 总页数和当前页，获得页码
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

# 创建评论
@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content should not be empty.')
    # 查找此评论的对应的博客是否存在
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog Not Found')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name,
                      user_image=user.image, content=content.strip())
    await comment.save()
    return comment

# 删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    logging.info(id)
    # 检查：有就删除，没有就抛出异常
    check_admin(request)
    comment = await Comment.find(id)
    if comment is None:
        raise APIResourceNotFoundError('comment')
    await comment.remove()
    return dict(id=id)
