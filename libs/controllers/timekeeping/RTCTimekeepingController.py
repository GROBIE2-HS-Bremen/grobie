from libs.controllers.timekeeping import ITimekeepingController

from time import mktime, localtime
from machine import RTC


class RTCTimekeepingController(ITimekeepingController):

    def __init__(self) -> None:
        super().__init__()

        self.rtc = RTC()

    def get_time(self):
        t = self.rtc.datetime()
        return mktime(t)  # type: ignore
    
    def sync_time(self, unix_timestamp: int):
        t = localtime(unix_timestamp)
        self.rtc.datetime(t)