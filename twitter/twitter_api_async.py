#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from tweepy import AppAuthHandler, API
from tweepy.error import TweepError

from localsettings import AUTH_DATA


class APIHandler(object):
    """docstring for APIHandler"""
    def __init__(self, auth_data, max_nreqs=10):
        self.auth_data = auth_data
        self.max_nreqs = max_nreqs
        self.tweets = {}
        self.feeds = {}

    def conn(self):
        if self.nreqs == self.max_nreqs:
            self.get_fresh_connection()
        else:
            self.nreqs += 1
        return self.conn_

    def get_fresh_connection(self, credential_index, uid):
        success = False
        while not success:
            try:
                d = self.auth_data[credential_index]
                print "Switching to API Credentials #%d" % credential_index

                auth = AppAuthHandler(d['consumer_key'], d['consumer_secret'])
                self.conn_ = API(
                    auth_handler=auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
                self.nreqs = 0
                return self.conn_
            except TweepError, e:
                print("Error trying to connect: %s" % e.message)
                time.sleep(10)

    def traer_seguidores(self, credential_index, uid, date_lower_limit, **kwargs):
        cursor = -1
        self.get_fresh_connection(credential_index, uid)
        while cursor:
            while True:
                try:
                    fs, (_, cursor) = self.conn_.followers_ids(count=5000, cursor=cursor, **kwargs)
                    self.feeds[uid] += fs
                    print "fetched %d followers so far." % len(self.feeds)
                except TweepError, e:
                    if 'rate limit' not in e.reason.lower():
                        raise e
                    else:
                        print e
                        print "Rate limit reached for this conexion"
                        # self.get_fresh_connection(credential_index, uid)
                        continue

    def traer_timeline(self, credential_index, uid, date_lower_limit):
        page = 1
        done = False
        self.get_fresh_connection(credential_index, uid)
        while not done:
            try:
                print "trying to fetch timeline for user with id={0}".format(uid)
                page_tweets = self.conn_.user_timeline(user_id=uid, page=page)
                if not page_tweets:
                    done = True
                    break
                for tw in page_tweets:
                    if tw.created_at < date_lower_limit:
                        done = True
                        break
                    else:
                        self.tweets[uid].append(tw._json)
                        print "Tweets for uid={0}".format(self.tweets[uid])
                page += 1
            except Exception, e:
                if e.message == u'Not authorized.':
                    break
                else:
                    print("Error: %s" % e.message)
                    # self.get_fresh_connection(credential_index, uid)
                    continue


API_HANDLER = APIHandler(AUTH_DATA)
