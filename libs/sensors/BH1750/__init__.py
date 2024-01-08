from libs.sensors import ISensor
from libs.sensors.BH1750.BH1750_base import BH1750_base

from machine import I2C

class BH1750(ISensor):

    def __init__(self, i2c: I2C) -> None:
        self._i2c = i2c

        self.bh = BH1750_base(address=0x23, i2c=self._i2c)

    def get_measurement(self) -> dict:
        return {
            'lumen': self.bh.measurement
        }