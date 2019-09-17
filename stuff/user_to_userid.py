from sophie_bot import mongodb

print(mongodb.blacklisted_users.update_many({'user': {'$exists': True}}, {"$rename": {'user': 'user_id'}}))

print(mongodb.gbanned_groups.update_many({'user': {'$exists': True}}, {"$rename": {'user': 'user_id', 'chat': 'chat_id'}}))