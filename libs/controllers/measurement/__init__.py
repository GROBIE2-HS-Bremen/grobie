from libs.controllers.measurement.Measurement import Measurement
from libs.controllers.timekeeping import ITimekeepingController
from libs.sensors import ISensor

import asyncio


class MeasurementController:

    def __init__(self, sensors: list[ISensor], timekeeping_controller: ITimekeepingController, actions: list) -> None:
        self.sensors = sensors
        self.actions = actions
        self.timekeeping_controller = timekeeping_controller

    def start(self, period: int = 1):
        loop = asyncio.get_event_loop()
        self.t = loop.create_task(self._start(period * 1000))

    def stop(self):
        self.t.cancel()

    async def _start(self, period: int = 1000):
        while True:
            await asyncio.sleep(period / 1000)
            self.measure()

    def measure(self):
        data = {}
        for sensor in self.sensors:
            data.update(sensor.get_measurement())

        measurement = Measurement(
            timestamp=self.timekeeping_controller.get_time(),
            data=data
        )
        measurement.data = data

        for action in self.actions:
            action(measurement)

        return measurement
