from libs.external.ChannelLogger import logger
from libs.sensors import ISensor

from machine import I2C

import os 


class I2CSensorFactory:
    """ # I2CSensorFactory
        this factory is used to create sensors connected to the I2C bus. it 
        will scan the I2C bus for addresses and will create a sensor based on
        the address. the address is used to find the folder.

        the folder name should start with the address in hex and uppercase
        followed by a _ and the name of the sensor. for example:
         - 23_BH1750
         - 76_BME280

        the folder should contain a __init__.py file which contains the Sensor
        class. this class should implement the ISensor interface.

        the factory will dynamicaly import the folder and create the sensor
        based on the address. If it cant find the folder it will return null
        if it finds more then one folder it will use the first one.

        the factory will return a list of sensors. if no sensors are found it
        will return an empty list.


        ## example:
        ```python
        from libs.sensors.SensorFactory import I2CSensorFactory
        from machine import I2C, Pin

        # connected are the BME280 and BH1750
        i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
        sensors = I2CSensorFactory.create_sensors(i2c)
        print(sensors)  # [<libs.sensors.BME280.Sensor object at 0x7f0c0d8c>, <libs.sensors.BH1750.Sensor object at 0x7f0c0d8c>]
        ```

        ## Notes: 
            - the factory makes use of the __import__ function which is normaly
                called by the import statement and is discouraged to use. however
                the other way to do this is to use the importlib module which is
                not available on micropython. the alternative is to use the
                exec() function but this should be avoided at all cost.

            - the factory will only look for folders in the libs/sensors folder.
                this is to prevent the factory from importing other files which
                are not sensors. this also means that the factory will only work
                if the sensors are in the libs/sensors folder.

            - the factory will only instantiate classes that implement the 
                ISensor interface. this is done by looking for a class that 
                implements the ISensor interface. if no class is found it will
                return None. if more then one class is found it will use the
                first one. this means that you shouldn't have more then one
                class in the __init__.py file. 
    """

    @staticmethod
    def create_sensors(i2c: I2C) -> list[ISensor]:
        """ Create sensors based on the I2C addresses found on the bus.
            this will scan the bus for addresses and will create a sensor
            based on the address. the address is used to find the module.
        """
        # find and create sensors based on the found addresses
        sensors = []
        for addr in i2c.scan():
            sensor = I2CSensorFactory.create_sensor(addr, i2c)
            if sensor is not None:
                sensors.append(sensor)
        
        return sensors

    @staticmethod
    def create_sensor(addr, i2c: I2C) -> ISensor | None:
        """ create a sensor based on the address. 
            this will dynamicaly import the folder which starts with the 
            supplied address
        """
        # convert the addr to hex and uppercase
        addr_str = hex(addr).replace('0x', '').upper() + '_'
        # get the folder that starts with that name
        folders = [f for f in os.listdir('libs/sensors') if f.startswith(addr_str)]

        if len(folders) == 0:
            return None
        
        # import and create the sensor
        # the __import__ is normaly called by the import statement and is 
        # discouraged to use. however the other way to do this is to use the 
        # importlib module which is not available on micropython. next to that 
        # see: https://docs.python.org/3/library/functions.html#import__
        s = __import__('libs.sensors.' + folders[0], globals(), locals(), [], 0)
        
        # find and construct the sensor
        # this is again dynamicly done by looking for a class that implements
        # the ISensor interface. 
        for f in dir(s):
            if f != 'ISensor' and isinstance(getattr(s, f), type):
                if issubclass(getattr(s, f), ISensor):
                    return getattr(s, f)(i2c)

        logger('No instance of ISensor found in module ' + folders[0], channel='info')
        return None
