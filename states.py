from enum import Enum

class States(Enum):
    asleep = 0
    awake_after_sleep = 1
    received_command = 2
    turned_on = 3
    turned_off = 4
    about_to_sleep = 5
    send_battery = 6
    no_state = 9