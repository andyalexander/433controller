import paho.mqtt.client as mqtt
import time
import json
from schedule import Schedule
from device import Device
from states import States
from datetime import timedelta, datetime

ip = "192.168.2.10"
user = "mqtt"
password = "mqtt"
client_id = "wateringHQ"

MESSAGE_LENGTH = 8
DEVICE_ID = 10

topic_sub = "home/OpenMQTTGateway_ESP8266_RF-CC1101/433toMQTT"
topic_pub = "home/OpenMQTTGateway_ESP8266_RF-CC1101/commands/MQTTto433"

def log(message, newLine = True):
    if newLine:
        print(message)
    else:
        print(message, end=" ")



def on_message(client, userdata, message):
    mess = json.loads(str(message.payload.decode("utf-8")))

    payload = str(mess['value']).zfill(MESSAGE_LENGTH)
    # dev_id, duration, state = Device.splitMessage(payload)
    # log("Device: {0}   Duration: {1}   State: {2}".format(dev_id, duration, state))
    device.handleEvent(payload)

def on_log(client, userdata, level, buf):
    print("log: ",buf)


def createSchedule():
    schedule = Schedule()
    # for x in range(5):
    #     t = datetime.now() + timedelta(minutes=x*4)
    #     e = schedule.addEventDateTime(time_on=t, duration=timedelta(minutes=1))
    #     print(e)
    t = datetime.now() + timedelta(minutes=1)
    e = schedule.addEventDateTime(time_on=t, duration=timedelta(minutes=1))
    print("Starting: {}".format(t), " duration: {}seconds".format(e['duration'].total_seconds()))

    return schedule


device = Device(DEVICE_ID)
device.schedule = createSchedule()
device.topic_publish = topic_pub

client = mqtt.Client(client_id)
client.username_pw_set(username=user, password=password)
# client.on_log = on_log
client.on_message = on_message          # set callback
device.mqtt_client = client

client.connect(ip)

client.loop_start()
client.subscribe(topic_sub)

while True:
    pass
client.loop_stop()