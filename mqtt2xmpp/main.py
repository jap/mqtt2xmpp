import logging
import time

import paho.mqtt.client as mqtt
from sleekxmpp import ClientXMPP
import yaml

log = logging.getLogger(__name__)


def main():
    with file("mqtt2xmpp.yaml") as f:
        config = yaml.load(f.read())

    logging.basicConfig(level=logging.WARNING)

    mqttc = mqtt.Client(userdata=config)
    mqttc.on_connect = on_mqtt_connect
    mqttc.on_message = on_mqtt_message
    mqttc.connect(config['mqtt']['host'], config['mqtt']['port'])

    xmppc = MQTT2XMPP(config['xmpp']['jid'], config['xmpp']['passwd'])
    xmppc.register_plugin('xep_0030') # Service Discovery
    xmppc.register_plugin('xep_0199')  # XMPP ping
    xmppc.connect()

    config['xmpp-client'] = xmppc

    mqttc.loop_start()
    xmppc.process()


class MQTT2XMPP(ClientXMPP):
    def __init__(self, jid, passwd):
        super(MQTT2XMPP, self).__init__(jid, passwd)
        self.subscribers = set([])
        self.status = {}
        self.flame = None
        self.room_temperature = None
        self.add_event_handler('session_start', self.session_start)
        self.add_event_handler('message', self.message)

    def session_start(self, event):
        self.get_roster()
        self.send_presence()

    def broadcast_message(self, mbody):
        for subscriber in self.subscribers:
            self.send_message(mto=subscriber, mbody=mbody)

    def set_status(self, key, value):
        self.status[key] = value

    def set_flame(self, flame):
        if flame == '1':
            self.flame = True
        else:
            self.flame = False
        self.send_presence()

    def set_room_temperature(self, room_temp):
        self.room_temp = room_temp
        self.send_presence()

    def send_presence(self):
        if self.flame:
            flame = u"\U0001F525 "
        else:
            flame = u""
        if self.room_temp:
            room_temp = self.room_temp
        else:
            room_temp = u"Unknown"
        super(MQTT2XMPP, self).send_presence(pstatus=u"%sRoom temperature: %s" %
                                             (flame, room_temp))

    def message(self, msg):
        body = msg['body']

        if body.startswith('talk'):
            self.subscribers.add(msg['from'].bare)
            msg.reply(body="Prepare to be spammed!").send()
        elif body.startswith('quiet'):
            self.subscribers.remove(msg['from'].bare)
            msg.reply(body="Ok, I'll shut up!").send()
        elif body.startswith('status'):
            status = "\n".join("%s:%s" % (key,val)
                               for key,val in self.status.iteritems())
            msg.reply(body=status).send()
        else:
            msg.reply(body="Don't know what to do with this message",
                      clear=False).send()

def on_mqtt_connect(client, config, flags, rc):
    log.debug("MQTT Connected rc=%r", rc)
    for topic in config['mqtt']['topics']:
        client.subscribe(topic)

def on_mqtt_message(client, config, msg):
    log.debug("MQTT got message: %s=%s", msg.topic, msg.payload)
    xmpp = config['xmpp-client']
    xmpp.set_status(msg.topic, msg.payload)

    if msg.topic == 'events/central_heating/otmonitor/roomtemperature':
        xmpp.set_room_temperature(msg.payload)
    if msg.topic == 'events/central_heating/otmonitor/flame':
        xmpp.set_flame(msg.payload)

    xmpp.broadcast_message("%s:%s" % (msg.topic, msg.payload))
