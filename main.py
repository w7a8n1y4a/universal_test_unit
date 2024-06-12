import time
from paho.mqtt import client as mqtt_client

from config import settings
from utils.utils import get_unit_topics, get_unit_uuid


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
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

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

    while True:
        for topic in unit_topics['output_topic']:
            msg = f"messages: {msg_count // 100} {msg_count}"
            topic = f'{settings.PEPEUNIT_URL}/output/{unit_uuid}/{topic}'
            result = client.publish(topic, msg)
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

        msg_count += 1

        time.sleep(1)

def run():
    client = connect_mqtt()

    client.loop_start()
    publish(client)
    client.loop_stop()

if __name__ == '__main__':
    run()
