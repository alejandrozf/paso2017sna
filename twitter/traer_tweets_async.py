#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent
import networkx as nx

from datetime import datetime

from twitter_api_async import API_HANDLER as TW

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

gevent_funcs = []

for _, uid in enumerate(uids):
    for credential_index in xrange(len(AUTH_DATA)):
        gevent_funcs.append(gevent.spawn(TW.traer_timeline, credential_index, uid, DESDE))

try:
    gevent.joinall(gevent_funcs)
except KeyboardInterrupt:
    pass
finally:
    TW.save_tweets()
