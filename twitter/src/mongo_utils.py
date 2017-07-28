from pymongo import MongoClient
import subprocess

client = MongoClient()

paso2017_sync = client.paso2017_sync

paso2017_async = client.paso2017_async


def print_collections_distribution(db):
    for coll_name in db.collection_names():
        coll = db.get_collection(coll_name)
        count = coll.find().count()
        if count > 0:
            print coll_name, coll.find().count()


def query_duplicate_elements(coll, field):
    return coll.aggregate([
        {'$group': {
            '_id': {field: "${0}".format(field)},
            'uniqueIds': {'$addToSet': '$_id'},
            'count': {'$sum': 1}
        }
        },
        {'$match': {
            'count': {"$gt": 1}
        }
        },
        {'$sort': {
            'count': -1
        }
        }])


def export_db(db, unified_file=False):
    for collection_name in db.collection_names():
        coll_count = db.get_collection(collection_name).find().count()
        if coll_count > 0:
            subprocess.call(
                "mongoexport -d {0} -c {1} -o {2}.json".format(
                    db.name, collection_name, collection_name), shell=True)
        if unified_file:
            subprocess.call("cat *.json > {0}".format(unified_file), shell=True)
