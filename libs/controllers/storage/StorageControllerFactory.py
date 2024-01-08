
from libs.controllers.storage import IStorageController
from libs.controllers.storage.LocalStorage import LocalStorageController
from libs.controllers.storage.SDCard import SDCardStorageController

from machine import SPI

class StorageControllerFactory:

    @staticmethod
    def get_controller(sck=None, mosi=None, miso=None, cs=None) -> IStorageController:
        """ get the storage controller """
        # check if any of the needed variables for a n SD card are not provided
        if sck is None or mosi is None or miso is None or cs is None: 
            return LocalStorageController()
        
        else: 
            # create the spi object
            spi = SPI(
                0, 
                baudrate=1000000, 
                polarity=0, 
                phase=0, 
                bits=8, 
                firstbit=SPI.MSB, 
                sck=sck, 
                mosi=mosi, 
                miso=miso
            )

            try:
                return SDCardStorageController(spi, cs)
            except OSError:
                return LocalStorageController()
        

