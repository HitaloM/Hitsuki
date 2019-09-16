from sophie_bot import mongodb

all_gbanned = mongodb.blacklisted_users.find({})
for gbanned in all_gbanned:
    if isinstance(gbanned['user'], str):
        mongodb.blacklisted_users.update_one({'_id': gbanned['_id']}, {"$set": {'user': int(gbanned['user'])}})
