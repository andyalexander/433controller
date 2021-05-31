from datetime import datetime, timedelta, date, time
from states import States

class Schedule():
    @staticmethod
    def _addTimedeltaToDate(dat: date, time_delta: timedelta):
        midnight = time(hour=0, minute=0, second=0)
        d_tmp = datetime.combine(dat, midnight)
        d_tmp += time_delta
        return d_tmp

    @staticmethod
    def getSecondsToStart(start_delta):
        time_to_start = Schedule._addTimedeltaToDate(date.today(), start_delta) - datetime.now()
        return time_to_start.total_seconds()

    def __init__(self):
        self.events = {}
        self.events_count = 0
        self.current_event = 0
        self.look_ahead_window = 60        # number of seconds ahead for event to treat as 'now'

    def addEvent(self, time_on: timedelta, duration: timedelta, state_to: States=States.turned_on):
        """
        Add event to list.

        :param time_on: timedelta object for offset since midnight
        :param duration: timedelta for length of event
        :param state_to: what this event changes to.  defaults to turn on.
        :return:
        """

        e = {"time_on": time_on, "duration": duration, "state_to": state_to}
        self.events[self.events_count] = e
        self.events_count += 1
        return e

    def addEventDateTime(self, time_on: datetime, duration: timedelta):
        t = timedelta(hours=time_on.hour, minutes=time_on.minute, seconds=time_on.second)
        e = self.addEvent(time_on=t, duration=duration)
        return e



    def getNextEvent(self):
        # if we are on a new day update the day
        # assume no event spans midnight!

        dt_now = datetime.now()

        if self.current_event < self.events_count:
            e = self.events[self.current_event]
            start_time = e['time_on']
            duration = e['duration']
            state = e['state_to']
            self.current_event += 1

            time_to_start = Schedule.getSecondsToStart(start_time)
            # check if the current event window has passed
            if time_to_start < - self.look_ahead_window:
                print('   - Event start window passed, skipping event')
            else:
                if abs(time_to_start)>self.look_ahead_window:           # leeway
                    duration = timedelta(seconds=time_to_start)
                    start_time = timedelta(hours=dt_now.hour, minutes=dt_now.minute, seconds=dt_now.second)  # timedelta for time now
                    state = States.turned_off
                    self.current_event -=1

                mins_to_start = int((Schedule._addTimedeltaToDate(date.today(), start_time) - dt_now).total_seconds() / 60)
        else:
            # sleep till midnight + 1 min (the 1 min is just to make sure we really are tomorrow ;) )
            timedelta_to_midnight = self._addTimedeltaToDate(date.today(), timedelta(days=1, minutes=1)) - dt_now
            start_time = timedelta(seconds=0)
            duration = timedelta_to_midnight
            state = States.turned_off
            self.current_event = 0                                  # reset current event as new day

            mins_to_start = int(timedelta_to_midnight.total_seconds()/60)


        duration = int(duration.total_seconds()/60)

        return (start_time, mins_to_start, duration, state)