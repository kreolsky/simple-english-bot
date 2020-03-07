import redis

# connect to Redis
server = redis.Redis(host="127.0.0.1", port=6379, db=0)

print(server.ping())
# should return True

# print(server.keys())
# # should return [] since we haven't added any keys yet
#
# print(server.get('MyKey'))
# # should return nothing since we haven't added the key yet
#
# print(server.set('MyKey', 'I love Python'))
# # should return True
#
#
# print(server.set('MyKey1', 'I love Python'))
# # should return True
#
# print(server.keys())
# # should return [b'MyKey']
#
# print(server.get('MyKey'))
# # should return "b'I love Python'"
#
# # print(server.delete('MyKey'))
# # should return 1 as success code
#
# # print(server.get('MyKey'))
# # should return nothing because we just deleted the key


# print(server.exists('MyKey10'))
print(server.keys())
# server.delete('en-ru:come off'.encode())
# server.flushdb()
