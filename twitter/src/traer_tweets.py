#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import networkx as nx

from datetime import date, datetime
from random import sample
from os.path import join

from twitter_api import API_HANDLER as TW

from localsettings import DATA_PATH

DATA_PATH = join(DATA_PATH, './reporte_07_26')

DIA = date(year=2017, month=7, day=18)

cuentas = [
    'HectorBaldassi',
    'MartinLlaryora',
]

gpath = join(DATA_PATH, 'red_cands5k.graphml')
g = nx.read_graphml(gpath)

uids = g.nodes()

# los candidatos al principio

cand_ids = ['845696348', '325778405']

[uids.remove(uid) for uid in cand_ids]

uids = cand_ids + uids

len(uids)

# Por ahora traemos tweets solo de 100 en cada audiencia

uids = []
uids += sample(g.predecessors(cand_ids[0]), 100)
uids += sample(g.predecessors(cand_ids[1]), 100)
uids = cand_ids + list(set(uids))

# fpath = join(DATA_PATH, "tl_uids.json")
# with open(fpath, "w") as f:
#     json.dump(uids, f)

# with open("tl_uids.json") as f:
#     uids = json.load(f)
len(uids)

tweets = {}
# with open('tweets_%s.json' % datetime.strftime(DIA, '%m-%d')) as f:
#     tweets = json.load(f)

for i, uid in enumerate(uids):
    if i % 5 == 0:
        perc = i * 100.0 / len(uids)
        print("%.1f %%" % perc)
    if uid in tweets:
        continue
    tweets[uid] = TW.traer_timeline(uid, dia=DIA)

len(tweets)

twpath = join(DATA_PATH, 'tweets_%s.json' % datetime.strftime(DIA, '%m-%d'))
with open(twpath, 'w') as f:
    json.dump(tweets, f)
