#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

__author__ = 'Toohoo Lee'

'''
JSON API definition.
'''

import json, logging, inspect, functools

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional)
    初始化数据
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.data = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self, field, message=''):
        # 超类，继承APIError中的基础错误类型的__init__(),传入参数error， data， message
        super(APIValueError, self).__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super(APIResourceNotFoundError, self).__init__('value:notfound', field, message)


class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, message=''):
        super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)
























