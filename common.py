import json

def encode(obj):
    return json.dumps(obj)

def decode(msg):
    return json.loads(msg)
