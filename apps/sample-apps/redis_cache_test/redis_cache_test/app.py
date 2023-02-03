import multiprocessing as mp
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import redis

things = {
    "ref15": {
        "color": "red",
        "price": 50.0,
        "quantity": 100,
        "purchased": 0,
    },
    "rf12": {
        "color": "blue",
        "price": 60.0,
        "quantity": 50,
        "purchased": 0,
    },
}

HOST = os.environ.get("REDIS_HOST")
PORT = int(os.environ.get("REDIS_PORT"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa N802
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        quantity = get_quantity()
        self.wfile.write(f"<html>quantity: {quantity}</html>".encode())


def server():
    with HTTPServer(("", 5000), Handler) as http:
        http.serve_forever()


def main():
    init()
    process = mp.Process(target=server)
    process.start()


def init():
    print(f"Redis host: {HOST}, port: {PORT}")
    init_db()
    quantity1 = get_quantity()
    print(f"quantity1: {quantity1}")
    test_db()
    quantity2 = get_quantity()
    print(f"quantity2: {quantity2}")


def init_db():
    base = redis.Redis(host=HOST, port=PORT, db=0)
    with base.pipeline() as pipe:
        for ref, info in things.items():
            for field, value in info.items():
                pipe.hset(ref, field, value)
        pipe.execute()
    base.bgsave()


def get_quantity() -> str:
    base = redis.Redis(host=HOST, port=PORT, db=0)
    ref = "ref15"
    info = base.hgetall(ref)
    return info[b"quantity"].decode("utf8")


def test_db() -> bool:
    base = redis.Redis(host=HOST, port=PORT, db=0)
    ref = "ref15"
    zero = b"0"
    with base.pipeline() as pipe:
        try:
            pipe.watch(ref)
            nleft: bytes = base.hget(ref, "quantity")
            if nleft > zero:
                pipe.multi()
                pipe.hincrby(ref, "quantity", -1)
                pipe.hincrby(ref, "purchased", 1)
                pipe.execute()
                flag = True
            else:
                pipe.unwatch()
                flag = False
        except redis.WatchError:
            flag = False
    return flag
