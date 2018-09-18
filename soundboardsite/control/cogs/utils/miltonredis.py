import redis
import json
import os

r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

def get_value(key):
    return r.get(key)

def set_value(key, value):
    r.set(key, value)

def get_json_value(key):
    return json.loads(r.get(key))

def set_json_value(key, value):
    r.set(key, json.dumps(value))

def get_list_value(key):
    return r.lrange(key, 0, -1)

def add_to_list(key, value):
    r.lpush(key, value)

def rem_from_list(key, value):
    r.lrem(key, value)