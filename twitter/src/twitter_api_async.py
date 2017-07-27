#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from collections import defaultdict
from datetime import datetime
from time import sleep
from os.path import join

from pymongo import MongoClient
from tweepy import AppAuthHandler, API
from tweepy.error import TweepError

from localsettings import AUTH_DATA, DATA_PATH

MONGO_HOST = 'mongodb://localhost/paso2017_async'


class APIHandler(object):
    """docstring for APIHandler"""
    def __init__(self, auth_data, max_nreqs=10):
        self.auth_data = auth_data
        self.max_nreqs = max_nreqs
        client = MongoClient(MONGO_HOST)
        self.tweets = client.paso2017_async
        # para marcar hasta la página actual que se han bajado tweets para cada usuario
        # y proseguir la bajada a partir de ahí
        self.tweets_active_pages = defaultdict(int)
        # para guardar los tiempos de bajada de tweets por usuario
        self.user_tweets_download_time = defaultdict(int)
        self.feeds = {}
        # guardamos las conexiones por credencial para poder reusarlas luego de ser necesario
        self.connections = {}
        self.threads = defaultdict(list)

    def num_user_tweets(self, uid):
        return self.tweets[uid].count()

    def num_total_tweets(self):
        count = 0
        for collection_name in self.tweets.collection_names():
            count += self.tweets.get_collection(collection_name).count()
        return count

    def save_tweets(API_HANDLER_instance, initial_day):
        twpath = join(DATA_PATH, 'tweets_async_%s.json' % datetime.strftime(initial_day, '%m-%d'))
        with open(twpath, 'w') as f:
            json.dump(API_HANDLER_instance.tweets, f)

    def get_fresh_connection(self, credential_index):
        success = False
        while not success:
            try:
                d = self.auth_data[credential_index]
                print "Switching to API Credentials #%d" % credential_index
                auth = AppAuthHandler(d['consumer_key'], d['consumer_secret'])
                self.connections[credential_index] = API(
                    auth_handler=auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
                return self.connections[credential_index]
            except TweepError, e:
                print("Error trying to connect: %s" % e.message)
                sleep(10)

    def set_connection(self, credential_index):
        if not self.connections.get(credential_index, False):
            self.get_fresh_connection(credential_index)
        # else:
        #     print "Using API Credential #{0}".format(credential_index)

    def traer_seguidores(self, credential_index, uid, date_lower_limit, **kwargs):
        cursor = -1
        self.set_connection(credential_index)
        while cursor:
            while True:
                try:
                    fs, (_, cursor) = self.connection[credential_index].followers_ids(
                        count=5000, cursor=cursor, **kwargs)
                    self.feeds[uid] += fs
                    print "fetched %d followers so far." % len(self.feeds)
                except TweepError, e:
                    if 'rate limit' not in e.reason.lower():
                        raise e
                    else:
                        print e
                        print "Rate limit reached for this conexion"

    def _end_uid_connection(self, uid, added_time=None):
        self.tweets_active_pages[uid] = -1
        for thread in self.threads[uid]:
            thread._Thread__stop()
        n_tweets_uid = self.tweets[uid].count()
        print "Done with uid:{0}, {1} tweets fetched ".format(uid, n_tweets_uid)

    def _add_tweets(self, uid, page_tweets, desde, hasta, validate=True):
        for tw in page_tweets:
            # print(tw.text)
            if validate and desde and tw.created_at.date() < desde:
                self._end_uid_connection(uid)
                return True     # hay que terminar la descarga de tweets
            if validate and hasta and tw.created_at.date() > hasta:
                continue
            tweet_doc = tw._json
            self.tweets[uid].update_one(tweet_doc, {'$set': tweet_doc}, upsert=True)
        return False

    def traer_timeline(self, uid, credential_index, n_pages=None, desde=None, hasta=None, dia=None):
        if self.tweets_active_pages[uid] != -1:
            # no se han terminado de cargar los tweets de este usuario
            done = False
            if dia:
                desde = dia
                hasta = dia
            self.set_connection(credential_index)
            while not done:
                try:
                    self.tweets_active_pages[uid] += 1
                    page = self.tweets_active_pages[uid]
                    print "uid={0}, page={1}, credential_index={2}".format(uid, page, credential_index)
                    if n_pages and page > n_pages:
                        break
                    page_tweets = self.connections[credential_index].user_timeline(
                        user_id=uid, page=page)
                    if not page_tweets:
                        break
                    if n_pages and page <= n_pages:
                        self._add_tweets(uid, page_tweets, None, None, validate=False)
                    else:
                        done = self._add_tweets(uid, page_tweets, desde, hasta)
                except Exception, e:
                    print("Error {0} processing id={1} with credential={2}:".format(
                        e.message, uid, credential_index))
                    if e.message == u'Not authorized.':
                        self._end_uid_connection(uid)
                        break
                    else:
                        # salvando el número de página de tweets bajados para retomar a partir de
                        # ahí en las nuevas bajadas
                        self.tweets_active_pages[uid] = page
                        print "Moving to another connection ..."
            return


API_HANDLER = APIHandler(AUTH_DATA)
