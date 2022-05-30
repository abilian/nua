#!/usr/bin/env python

import zmq
from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol, JSONRPCError
from tinyrpc.transports.zmq import ZmqClientTransport


ctx = zmq.Context()
ADDRESS = "127.0.0.1"
PORT = "5001"

rpc_client = RPCClient(
    JSONRPCProtocol(), ZmqClientTransport.create(ctx, f"tcp://{ADDRESS}:{PORT}")
)

remote_server = rpc_client.get_proxy()

print("----------------")
print("remote_server.test_add(2, 5)")
result = remote_server.test_add(2, 5)
print("response:", result)

# print("----------------")
# print('rpc_client.call("test_divide", [3, 0], {})')
# try:
#     result = rpc_client.call("test_divide", [3, 0], {})
# except JSONRPCError as e:
#     result = None
#     print(e._jsonrpc_error_code, e.message)
#     if hasattr(e, "data"):
#         print("data:", e.data)
# print(result)

print("----------------")
print("remote_server.test_divide(5, 0)")
try:
    result = remote_server.test_divide(5, 0)
except JSONRPCError as e:
    result = None
    print("Error:", e._jsonrpc_error_code, e.message)
    if hasattr(e, "data"):
        print("data:", e.data)
print(result)


print("----------------")
print("remote_server.user_count()")
result = remote_server.user_count()
print("response:", result)

print("----------------")
print("remote_server.user_list()")
result = remote_server.user_list()
print("response:", result)

print("----------------")
print("remote_server.user_delete_all()")
result = remote_server.user_delete_all()
print("response:", result)

print("----------------")
print("remote_server.user_count()")
result = remote_server.user_count()
print("response:", result)

print("----------------")
user_data = {
    "username": "user_1",
    "email": "foo1@exemple.com",
    "password": "azerty",
    "salt": "some_salt_string",
}
print("remote_server.user_add(user_data)")
result = remote_server.user_add(user_data)
print("response:", result)

print("----------------")
user_data = {
    "username": "user_2",
    "email": "foo2@exemple.com",
    "password": "azerty",
    "salt": "some_salt_string",
}
print("remote_server.user_add(user_data)")
result = remote_server.user_add(user_data)
print("response:", result)

print("----------------")
user_data = {
    "username": "user_3",
    "email": "foo@exemple.com",
    "password": "azerty",
    "salt": "some_salt_string",
}
print("remote_server.user_add(user_data)")
result = remote_server.user_add(user_data)
print("response:", result)

print("----------------")
print("remote_server.user_count()")
result = remote_server.user_count()
print("response:", result)

print("----------------")
print("remote_server.user_list()")
result = remote_server.user_list()
print("response:", result)
