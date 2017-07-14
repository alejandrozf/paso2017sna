#!/usr/bin/env python
# -*- coding: utf-8 -*-

import networkx as nx
import json

from datetime import datetime

from twitter_api_async import API_HANDLER as TW
from twisted.internet import reactor

from localsettings import AUTH_DATA

DESDE = datetime(year=2017, month=7, day=13)

cuentas = [
    'HectorBaldassi',
    'MartinLlaryora',
]

g = nx.read_graphml('red_cands.graphml')

uids = g.nodes()

# los candidatos al principio
cand_ids = ['845696348', '325778405']

[uids.remove(uid) for uid in cand_ids]

uids = cand_ids + uids

for uid in enumerate(uids):
    for credential_index in xrange(len(AUTH_DATA)):
        reactor.callWhenRunning(TW.traer_timeline, credential_index, uid, DESDE)

# 1 día de tweets, 28k usuarios, 7hs (a tener en cuenta ...), inspeccionar 'tw_handler.tweets'

reactor.run()

for uid, value in TW.tweets.items():
    with open('tweets_%s.json' % uid, 'w') as f:
        json.dump(value, f)     # TODO: revisar posible duplicación de tweets
