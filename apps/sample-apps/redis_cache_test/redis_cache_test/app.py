import os

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


def main():
    host = os.environ.get("REDIS_HOST")
    port = int(os.environ.get("REDIS_PORT"))
    print(f"Redis host: {host}, port: {port}")
    init_db(host, port, 0)
    quantity1 = get_quantity(host, port, 0)
    print(f"quantity1: {quantity1}")
    test_db(host, port, 0)
    quantity2 = get_quantity(host, port, 0)
    print(f"quantity2: {quantity2}")


def init_db(host: str, port: int, db: int):
    base = redis.Redis(host=host, port=port, db=db)
    with base.pipeline() as pipe:
        for ref, info in things.items():
            pipe.hset(ref, info)
        pipe.execute()
    base.bgsave()


def get_quantity(host: str, port: int, db: int):
    base = redis.Redis(host=host, port=port, db=db)
    ref = "ref15"
    info = base.hgetall(ref)
    return info["quantity"]


def test_db(host: str, port: int, db: int) -> bool:
    base = redis.Redis(host=host, port=port, db=db)
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
