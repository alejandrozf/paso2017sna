#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import gevent

from collections import defaultdict
from datetime import datetime
from time import time, sleep
from os.path import join

from tweepy import AppAuthHandler, API
from tweepy.error import TweepError

from localsettings import AUTH_DATA, DATA_PATH


class APIHandler(object):
    """docstring for APIHandler"""
    def __init__(self, auth_data, max_nreqs=10):
        self.auth_data = auth_data
        self.max_nreqs = max_nreqs
        self.tweets = defaultdict(list)
        # para marcar hasta la página actual que se han bajado tweets para cada usuario
        # y proseguir la bajada a partir de ahí
        self.tweets_active_pages = defaultdict(int)
        # para guardar los tiempos de bajada de tweets por usuario
        self.user_tweets_download_time = defaultdict(int)
        self.feeds = {}
        # guardamos las conexiones por credencial para poder reusarlas luego de ser necesario
        self.connections = {}

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
                        gevent.sleep(0)

    def _end_uid_connection(self, uid):
        self.tweets_active_pages[uid] = -1
        # n_tweets_uid = len(self.tweets[uid])
        # print "Done with uid:{0}, {1} tweets fetched ".format(uid, n_tweets_uid)

    def _add_tweets(self, uid, page_tweets, desde, hasta):
        for tw in page_tweets:
            # print(tw.text)
            if desde and tw.created_at.date() < desde:
                self._end_uid_connection(uid)
                return True     # hay que terminar la descarga de tweets
            if hasta and tw.created_at.date() > hasta:
                continue
            self.tweets[uid].append(tw._json)
        return False

    def traer_timeline(self, uid, credential_index, desde=None, hasta=None, dia=None):
        if self.tweets_active_pages[uid] != -1:
            # no se han terminado de cargar los tweets de este usuario
            user_init_time = time()
            done = False
            if dia:
                desde = dia
                hasta = dia
            self.set_connection(credential_index)
            connection_stablished_time = time()
            self.user_tweets_download_time[uid] += connection_stablished_time - user_init_time
            while not done:
                try:
                    self.tweets_active_pages[uid] += 1
                    page = self.tweets_active_pages[uid]
                    # print page, uid
                    attempt_initial_time = time()
                    page_tweets = self.connections[credential_index].user_timeline(
                        user_id=uid, page=page)
                    if not page_tweets:
                        self._end_uid_connection(uid)
                        break
                    done = self._add_tweets(uid, page_tweets, desde, hasta)
                    self.user_tweets_download_time[uid] += time() - attempt_initial_time
                except Exception, e:
                    self.user_tweets_download_time[uid] += time() - attempt_initial_time
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
                        gevent.sleep(0)


API_HANDLER = APIHandler(AUTH_DATA)
