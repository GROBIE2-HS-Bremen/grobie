from libs.sensors import ISensor
from libs.sensors.BME280.BME280_base import BME280_base

from machine import I2C

class BME280(ISensor):

    def __init__(self, i2c: I2C) -> None:
        self._i2c = i2c

        self.bme = BME280_base(i2c=self._i2c)

    def get_measurement(self) -> dict:
        return {
            'temperature': self.bme.temperature,
            'humidity': self.bme.humidity,
            'pressure': self.bme.pressure
        }
