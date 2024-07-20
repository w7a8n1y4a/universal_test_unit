import json
import time
import psutil
import binascii

from config import settings


def get_unit_uuid(token: str):
    data = token.split('.')[1].encode()
    return json.loads(binascii.a2b_base64(data + (len(data) % 4) * b'=').decode('utf-8'))['uuid']


def get_unit_schema():
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

def get_input_topics() -> list[str]:
    schema_dict = get_unit_schema()

    input_topics = []
    for topic_type in schema_dict.keys():
        if topic_type.find('input') >= 0:
            for topic in schema_dict[topic_type].keys():
                input_topics.extend(schema_dict[topic_type][topic])
    
    return input_topics

def pub_output_topic_by_name(client, topic_name: str, message: str) -> None:
    schema_dict = get_unit_schema()

    if topic_name not in schema_dict['output_topic'].keys():
        raise KeyError('Not topic in schema')

    for topic in schema_dict['output_topic'][topic_name]:
        result = client.publish(topic, message)

        if result[0] == 0:
            print(f"Send `{message}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

def search_topic_in_schema(schema_dict: dict, node_uuid: str) -> tuple[str, str]:

    for topic_type in schema_dict.keys():
        for topic_name in schema_dict[topic_type].keys():
            for topic in schema_dict[topic_type][topic_name]:
                if topic.find(node_uuid) >= 0:
                    return (topic_type, topic_name)

    raise ValueError
