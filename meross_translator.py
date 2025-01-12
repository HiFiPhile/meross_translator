#!/usr/bin/env python3

import hashlib
import logging
import random
import time
import json
import argparse
import sys

from paho.mqtt import client as mqtt_client

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def connect_mqtt(address, port, ca=None, username=None, password=None):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Connected to MQTT Broker!')
        else:
            logging.error(f'Failed to connect, return code {rc}')

    client = mqtt_client.Client()
    if ca is not None:
        client.tls_set(ca_certs=ca)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(address, port)
    return client


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60


def on_disconnect(client, userdata, rc):
    logging.error('Disconnected with result code: %s', rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info('Reconnecting in %d seconds...', reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info('Reconnected successfully!')
            return
        except Exception as err:
            logging.error('%s. Reconnect failed. Retrying...', err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.error('Reconnect failed after %s attempts. Exiting...', reconnect_count)


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        logging.info(f'Received {msg.payload.decode()}')
        try:
            cmd = json.loads(msg.payload.decode())

            data = {}
            data['header'] = {}
            data['header']['from'] = '/app/0-'+cmd['uuid']+'/subscribe'
            data['header']['messageId'] = str(random.randbytes(16).hex())
            data['header']['method'] = 'SET'
            data['header']['namespace'] = cmd['namespace']
            data['header']['payloadVersion'] = 1
            data['header']['timestamp'] = int(time.time())
            stringToHash = data['header']['messageId'] + str(data['header']['timestamp'])
            hash = hashlib.md5(stringToHash.encode())
            data['header']['sign'] = hash.hexdigest()
            data['payload'] = cmd['payload']

            send = json.dumps(data)
            topic = '/appliance/'+cmd['uuid']+'/subscribe'
            logging.info(f'Send {send} to {topic}')
            client.publish(topic, send)
        except Exception as e:
            logging.error(e)

    client.subscribe('meross/translator')
    client.on_message = on_message


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='MQTT broker host address', type=str, required=True)
    parser.add_argument('-p', '--port', help='MQTT broker port', type=int, required=False, default=8883)
    parser.add_argument('-u', '--user', help='MQTT user', type=str, required=False)
    parser.add_argument('-P', '--password', help='MQTT password', type=str, required=False)
    parser.add_argument('-c', '--ca', help='CA file for TLS connection', required=False, default=None)
    args = parser.parse_args()
    
    client = connect_mqtt(args.address, args.port, args.ca, args.user, args.password)
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
