#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import gevent
import networkx as nx

from datetime import date
from os.path import join
from random import sample
from time import time

from twitter_api_async import API_HANDLER as TW

from localsettings import AUTH_DATA, DATA_PATH

DATA_PATH = join(DATA_PATH, './reporte_07_26')

DESDE = date(year=2017, month=7, day=21)
HASTA = date(year=2017, month=7, day=23)

cuentas = [
    'HectorBaldassi',
    'MartinLlaryora',
]

init_total_time = time()

gpath = join(DATA_PATH, 'red_cands5k.graphml')
g = nx.read_graphml(gpath)

uids = g.nodes()

# los candidatos al principio

cand_ids = ['845696348', '325778405']

[uids.remove(uid) for uid in cand_ids]

uids = cand_ids + uids

# Por ahora traemos tweets solo de 100 en cada audiencia

uids = []
# uids += sample(g.predecessors(cand_ids[0]), 100)
# uids += sample(g.predecessors(cand_ids[1]), 100)
uids += g.predecessors(cand_ids[0])[:100]
uids += g.predecessors(cand_ids[1])[:100]
uids = cand_ids + list(set(uids))

# fpath = join(DATA_PATH, "tl_uids.json")
# with open(fpath, "w") as f:
#     json.dump(uids, f)

# with open("tl_uids.json") as f:
#     uids = json.load(f)

tweets = {}
# with open('tweets_%s.json' % datetime.strftime(DIA, '%m-%d')) as f:
#     tweets = json.load(f)
n_tweets = 0
users_time = []

gevent_funcs = []

n_auth_data = len(AUTH_DATA)
credential_index_list = sample(xrange(n_auth_data), n_auth_data)

for _, uid in enumerate(uids):
    for credential_index in credential_index_list:
        gevent_funcs.append(
            gevent.spawn(TW.traer_timeline, uid, credential_index, desde=DESDE, hasta=HASTA))

try:
    gevent.joinall(gevent_funcs)
except KeyboardInterrupt:
    pass
finally:
    n_tweets = sum([len(value) for value in TW.tweets.values()])
    n_users = len(uids)
    total_time = time() - init_total_time
    avg_tweets_per_user = n_tweets / n_users
    avg_time_per_tweet = total_time / n_tweets
    avg_user_time = sum(TW.user_tweets_download_time.values()) / len(TW.user_tweets_download_time)

    print "Tiempo total: {0} segundos".format(total_time)
    print "Cantidad media de tweets por usuario: {0}".format(avg_tweets_per_user)
    print "Tiempo promedio de descarga de cada tweet: {0} segundos".format(avg_time_per_tweet)
    print "Tiempo promedio de descarga de todos los tweets de un usuario: {0} segundos".format(
        avg_user_time)

    print "Guardando {0} tweets ...".format(n_tweets)
    TW.save_tweets(DESDE)
