import json
import time
import psutil
import binascii

from config import settings


def get_unit_uuid(token: str):
    data = token.split('.')[1].encode()
    return json.loads(binascii.a2b_base64(data + (len(data) % 4) * b'=').decode('utf-8'))['uuid']



def get_unit_topics():
    with open('schema.json', 'r') as f:
        return json.loads(f.read())


def get_topic_split(topic):
    return tuple(topic.split('/'))


def get_unit_state():
    memeory_info = psutil.virtual_memory()

    state_dict = {
        'millis': round(time.time() * 1000),
        'mem_free': memeory_info.available,
        'mem_alloc': memeory_info.total - memeory_info.available,
        'freq': psutil.cpu_freq().current,
        'commit_version': settings.COMMIT_VERSION
    }
    return json.dumps(state_dict)
