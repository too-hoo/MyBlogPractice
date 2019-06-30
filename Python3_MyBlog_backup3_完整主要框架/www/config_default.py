#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

'''
Default configurations.
'''

__author__ = 'Toohoo Lee'

configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'toohoo',
        'password': '123',
        'db': 'myblogdb'
    },
    'session': {
        'secret': 'Myblogdb'
    }
}
