#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey, sleep; monkey.patch_all()
# import traceback

from collections import defaultdict
from random import choice

from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from tweepy import AppAuthHandler, API
from tweepy.error import TweepError

from localsettings import AUTH_DATA

MONGO_HOST = 'mongodb://localhost/paso2017_async'


class APIHandler(object):
    """docstring for APIHandler"""
    def __init__(self, auth_data, max_nreqs=10):
        self.auth_data = auth_data
        self.index = choice(range(len(auth_data)))
        client = MongoClient(MONGO_HOST)
        self.tweets = client.paso2017_async
        # para marcar hasta la página actual que se han bajado tweets para cada usuario
        # y proseguir la bajada a partir de ahí
        self.tweets_active_pages = defaultdict(lambda: 1)
        # para guardar los tiempos de bajada de tweets por usuario
        self.feeds = {}
        # guardamos las conexiones por credencial para poder reusarlas luego de ser necesario
        self.connections = {}

    def num_user_tweets(self, uid):
        return self.tweets[uid].count()

    def num_total_tweets(self):
        count = 0
        for collection_name in self.tweets.collection_names():
            count += self.tweets.get_collection(collection_name).count()
        return count

    def get_fresh_connection(self):
        while True:
            try:
                self.index = (self.index + 1) % len(self.auth_data)
                if not self.connections.get(self.index, False):
                    d = self.auth_data[self.index]
                    print "Switching to API Credentials #%d" % self.index
                    auth = AppAuthHandler(d['consumer_key'], d['consumer_secret'])
                    self.connections[self.index] = API(
                        auth_handler=auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
                return self.connections[self.index]
            except TweepError, e:
                print("Error trying to connect: %s" % e.message)
                sleep(10)

    def _end_uid_connection(self, uid):
        self.tweets_active_pages[uid] = -1
        # n_tweets_uid = len(self.tweets[uid])
        # print "Done with uid:{0}, {1} tweets fetched ".format(uid, n_tweets_uid)

    def _add_tweets(self, uid, page_tweets, desde, hasta):
        self.tweets[uid].create_index([('id_str', ASCENDING)], unique=True)
        for tw in page_tweets:
            # print(tw.text)
            if desde and tw.created_at.date() < desde:
                self._end_uid_connection(uid)
                return True     # hay que terminar la descarga de tweets
            if hasta and tw.created_at.date() > hasta:
                continue
            tweet_doc = tw._json
            try:
                self.tweets[uid].update_one(tweet_doc, {'$set': tweet_doc}, upsert=True)
            except DuplicateKeyError:
                # print "Found duplicate tweet {0}".format(tweet_doc['text'].encode('utf-8'))
                pass
        return False

    def traer_timeline(self, uid, n_pages=None, desde=None, hasta=None, dia=None):
        if self.tweets_active_pages[uid] != -1:
            # no se han terminado de cargar los tweets de este usuario
            done = False
            if dia:
                desde = dia
                hasta = dia
            connection = self.get_fresh_connection()
            while not done:
                try:
                    page = self.tweets_active_pages[uid]
                    if n_pages and page > n_pages:
                        break
                    # print "uid={0}, page={1}, credential={2}".format(uid, page, self.index)
                    page_tweets = connection.user_timeline(
                        user_id=uid, page=page)
                    if not page_tweets:
                        break
                    if n_pages and page <= n_pages:
                        self._add_tweets(uid, page_tweets, False, False)
                    else:
                        done = self._add_tweets(uid, page_tweets, desde, hasta)
                    self.tweets_active_pages[uid] += 1
                except Exception, e:
                    # traceback.print_exc()
                    print("Error {0}: processing id={1} with credential={2}".format(
                        e, uid, self.index))
                    if e.message == u'Not authorized.':
                        self._end_uid_connection(uid)
                        break
                    else:
                        print "Moving to another connection ..."
                        connection = self.get_fresh_connection()
                        sleep(0)


API_HANDLER = APIHandler(AUTH_DATA)
