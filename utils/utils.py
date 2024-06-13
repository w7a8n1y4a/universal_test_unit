import json

import binascii


def get_unit_uuid(token: str):
    data = token.split('.')[1].encode()
    return json.loads(binascii.a2b_base64(data + (len(data) % 4) * b'=').decode('utf-8'))['uuid']



def get_unit_topics():
    with open('schema.json', 'r') as f:
        return json.loads(f.read())


def get_topic_split(topic):
    return tuple(topic.split('/'))

