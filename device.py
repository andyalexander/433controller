from schedule import Schedule
from states import States
from datetime import datetime, date, timedelta
import paho.mqtt.client as mqtt

class Device():

    def __init__(self, device_id: int):
        self.device_id = device_id
        self.schedule = Schedule()
        self.current_state = States.no_state

        self.mqtt_client = None
        self.topic_publish = None

        self.last_message = None

    def set_state(self, target_state: States, payload=0):
        v = self.device_id * 1000000
        v += payload * 10
        v += target_state.value
        v = int(v)                                      # make sure this is an int
        v = str(v).zfill(8)

        payload = '{{ "value": {} }}'.format(v)

        # check if this is a duplicate message, handles the multi-echo problem.
        # TODO: add timestamp / crc to message
        if self.last_message != payload:
            self.current_state = target_state
            print("Setting state to: {}".format(self.current_state))

            self.mqtt_client.publish(self.topic_publish, payload=payload)
            print("Sent message: {}".format(payload))

            self.last_message = payload

    @staticmethod
    def splitMessage(payload):
        device_id = int(payload[0:2])
        duration = int(payload[2:7])
        state = int(payload[7])
        return (device_id, duration, state)

    def handleEvent(self, event_value: str):
        id, duration, state = Device.splitMessage(event_value)

        if id == self.device_id:
            # print('Message from device: {0} : {1}'.format(id, event_value))

            if state == States.send_battery.value:
                print("  - Battery: {}volts".format(float(duration)/1000))

            if state == States.no_state.value:
                print("  - No state")
                self.set_state(States.turned_off)

            if state == States.turned_off.value:
                print("  - Turning off for: {}mins".format(duration))

            if state == States.turned_on.value:
                print("  - Turning on for: {}mins".format(duration))

            if state == States.about_to_sleep.value:
                print("  - About to sleep for: {}mins".format(duration))

            if state == States.awake_after_sleep.value:
                print("  - Woke up")
                self.set_state(States.turned_off)

                next_start, next_mins_to_start, next_duration, next_state = self.schedule.getNextEvent()

                if next_mins_to_start <= int(self.schedule.look_ahead_window / 60):  # if start within n mins, then just start now
                    print("  - Time within event start window...")
                    time_to_wait = next_duration
                else:  # else pause till the next time
                    time_to_wait = next_mins_to_start
                    next_state = States.turned_off

                print("Next state: {0}  for time: {1}".format(next_state, time_to_wait))
                self.set_state(next_state, time_to_wait)

