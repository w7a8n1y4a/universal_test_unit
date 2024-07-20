import os
import shutil
import sys
import time
import uuid
import json
import httpx
import logging

import zlib

from paho.mqtt import client as mqtt_client

from config import settings
from utils.utils import get_unit_schema, get_unit_uuid, get_topic_split, get_unit_state, get_input_topics, pub_output_topic_by_name, search_topic_in_schema


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

        client.subscribe([(topic, 0) for topic in get_input_topics()])

    def on_message(client, userdata, msg):

        struct_topic = get_topic_split(msg.topic)
        print(struct_topic)

        if len(struct_topic) == 5:

            backend_domain, destination, unit_uuid, topic_name, *_ = get_topic_split(msg.topic)

            if destination == 'input_base_topic' and topic_name == 'update':

                new_version = json.loads(msg.payload.decode())['NEW_COMMIT_VERSION']
                if settings.COMMIT_VERSION != new_version:

                    headers = {
                        'accept': 'application/json',
                        'x-auth-token': settings.PEPEUNIT_TOKEN.encode()
                    }

                    wbits = 9
                    level = 9

                    url = f'https://{settings.PEPEUNIT_URL}/pepeunit/api/v1/units/firmware/tgz/{get_unit_uuid(settings.PEPEUNIT_TOKEN)}?wbits={str(wbits)}&level={str(level)}'
                    r = httpx.get(url=url, headers=headers)

                    filepath = f'tmp/update.tgz'
                    with open(filepath, 'wb') as f:
                        print(filepath)
                        f.write(r.content)

                    shutil.rmtree('tmp/update', ignore_errors=True)

                    new_version_path = 'tmp/update'

                    os.mkdir(new_version_path)

                    with open(filepath, 'rb') as f:

                        producer = zlib.decompressobj(wbits=wbits)
                        tar_data = producer.decompress(f.read()) + producer.flush()

                        tar_filepath = 'tmp/update.tar'
                        with open(tar_filepath, 'wb') as tar_file:
                            tar_file.write(tar_data)

                        shutil.unpack_archive(tar_filepath, new_version_path, 'tar')

                    shutil.copytree(new_version_path, './', dirs_exist_ok=True)
                    logging.info("I'll be back")

                    os.execl(sys.executable, *([sys.executable] + sys.argv))

            if destination == 'input_base_topic' and topic_name == 'schema_update':
                headers = {
                    'accept': 'application/json',
                    'x-auth-token': settings.PEPEUNIT_TOKEN.encode()
                }

                url = f'https://{settings.PEPEUNIT_URL}/pepeunit/api/v1/units/get_current_schema/{get_unit_uuid(settings.PEPEUNIT_TOKEN)}'
                r = httpx.get(url=url, headers=headers)

                with open('schema.json', 'w') as f:
                    f.write(json.dumps(json.loads(r.json()), indent=4))
                
                logging.info("Schema is Updated")
                logging.info("I'll be back")
                os.execl(sys.executable, *([sys.executable] + sys.argv))
        elif len(struct_topic) == 3:
            schema_dict = get_unit_schema()
            
            topic_type, topic_name = search_topic_in_schema(schema_dict, struct_topic[1])
            
            if topic_type == 'input_topic' and topic_name == 'input/pepeunit':
                
                print('Success load input state')
                value = msg.payload.decode()
                
                value = int(value)
                
                with open('log.json', 'w') as f:
                    f.write(json.loads({'value': value, 'input_topic': struct_topic}))
                
                for topic_name in schema_dict['output_topic'].keys():
                    pub_output_topic_by_name(client, schema_dict['output_topic']['output/pepeunit'], str(value))

    def on_subscribe(client, userdata, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1)

    client.username_pw_set(settings.PEPEUNIT_TOKEN, '')
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    client.connect(settings.MQTT_URL, 1883)
    return client

def publish(client):
    msg_count = 1

    schema_dict = get_unit_schema()

    last_state_pub = time.time()
    last_pub = time.time()
    while True:
        if (time.time() - last_pub) >= settings.DELAY_PUB_MSG:
            for topic in schema_dict['output_topic'].keys():

                msg = f"messages: {msg_count // 10}"
                pub_output_topic_by_name(client, topic, msg)

            msg_count += 1
            last_pub = time.time()

        if (time.time() - last_state_pub) >= settings.STATE_SEND_INTERVAL:
            
            topic = schema_dict['output_base_topic']['state/pepeunit'][0]
            msg = get_unit_state()

            result = client.publish(topic, msg)
            status = result[0]

            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

            last_state_pub = time.time()

        time.sleep(1)

def run():
    client = connect_mqtt()

    client.loop_start()
    publish(client)
    client.loop_stop()

if __name__ == '__main__':
    run()
