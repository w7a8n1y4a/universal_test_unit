import os
import shutil
import sys
import time
import json
import httpx
import logging

import zlib

from paho.mqtt import client as mqtt_client

from config import settings
from utils.utils import get_unit_topics, get_unit_uuid, get_topic_split, get_unit_state


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

        unit_uuid = get_unit_uuid(settings.PEPEUNIT_TOKEN)
        unit_topics = get_unit_topics()

        topics_sub = []
        for input_topic in unit_topics['input_topic']:
            topics_sub.append((f'{settings.PEPEUNIT_URL}/input/{unit_uuid}/{input_topic}', 0))

        for input_topic in unit_topics['input_base_topic']:
            topics_sub.append((f'{settings.PEPEUNIT_URL}/input_base/{unit_uuid}/{input_topic}', 0))

        client.subscribe(topics_sub)

    def on_message(client, userdata, msg):
        backend_domain, destination, unit_uuid, topic_name, *_ = get_topic_split(msg.topic)

        if destination == 'input_base' and topic_name == 'update':

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

    unit_topics = get_unit_topics()
    unit_uuid = get_unit_uuid(settings.PEPEUNIT_TOKEN)

    last_state_pub = time.time()
    last_pub = time.time()
    while True:
        if (time.time() - last_pub) >= settings.DELAY_PUB_MSG:
            for topic in unit_topics['output_topic'][:1]:
                msg = f"messages: {msg_count // 100} {msg_count}"
                topic = f'{settings.PEPEUNIT_URL}/output/{unit_uuid}/{topic}'
                result = client.publish(topic, msg)
                status = result[0]
                if status == 0:
                    print(f"Send `{msg}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")

            msg_count += 1
            last_pub = time.time()

        if (time.time() - last_state_pub) >= settings.STATE_SEND_INTERVAL:

            msg = get_unit_state()
            topic = f"{settings.PEPEUNIT_URL}/output_base/{unit_uuid}/{unit_topics['output_base_topic'][0]}"

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
