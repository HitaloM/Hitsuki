from sophie_bot import mongodb

check = mongodb.chat_list.find()
F = 0
for chat in check:
    F += 1
    if 'user_id' in chat:
        mongodb.chat_list.delete_one({'_id': chat['_id']})
        print(f"{F} deleted")
