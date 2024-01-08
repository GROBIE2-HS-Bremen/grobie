from libs.sensors.BH1750 import BH1750
from libs.sensors.BME280 import BME280
from machine import I2C


class I2CSensorFactory: 
    
    @staticmethod
    def create_sensors(i2c: I2C):
        # find and create sensors based on the found addresses
        return [I2CSensorFactory.getSensorFromAddr(addr)(i2c) for addr in i2c.scan()]

    @staticmethod
    def create_sensor(addr, i2c: I2C):
        sens = None
        
        # check if addr is a string or int. if string, get sensor from name, else get sensor from addr
        if isinstance(addr, str):
            sens = I2CSensorFactory.getSensorFromName(addr)
        else:
            sens = I2CSensorFactory.getSensorFromAddr(addr)

        return sens(i2c)  # construct the sensor 

    @staticmethod
    def getSensorFromAddr(addr):
        return {
            0x23: BH1750,
            0x76: BME280,
        }[addr]
    
    @staticmethod
    def getSensorFromName(name):
        return {
            'bh1750': BH1750,
            'bme280': BME280,
        }[name]
