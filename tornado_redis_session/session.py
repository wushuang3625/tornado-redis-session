# coding:utf-8
import base64

import M2Crypto
import redis
from tornado.web import RequestHandler


class SessionManager(object):
    def __init__(self, redis):
        self.redis = redis

    def set_session(self, sessionid, identifier, ctx):
        pipe = self.redis.pipeline()
        pipe.hset("session:%s" % sessionid, identifier, ctx)
        pipe.expire("session:%s" % sessionid, 3600)
        pipe.execute()

    def get_session(self, sessionid, identifier):
        ctx = self.redis.hget("session:%s" % sessionid, identifier)
        if ctx:
            self.redis.expire("session:%s" % sessionid, 3600)
        return ctx

    def clear(self, sessionid, identifier):
        self.redis.hdel("session:%s" % sessionid, identifier)

    def clear_all(self, sessionid):
        self.redis.delete("session:%s" % sessionid)


class RedisSessionHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        super(RedisSessionHandler, self).__init__(*args, **kwargs)
        _redis = redis.Redis(**self.settings['db'])
        self.__session_manager = SessionManager(_redis)

    def get_sessionid(self):
        return self.get_cookie('tsessionid')

    def __gen_sessionid(self):
        return base64.b64encode(M2Crypto.m2.rand_bytes(16))

    def get_session(self, key):
        sessionid = self.get_sessionid()
        if sessionid:
            return self.__session_manager.get_session(sessionid, key)

    def set_session(self, key, value):
        sessionid = self.get_sessionid()
        if not sessionid:
            sessionid = self.__gen_sessionid()
            self.set_cookie('tsessionid', sessionid)

        return self.__session_manager.set_session(sessionid, key, value)