from machine import SPI, Pin
from libs.controllers.storage.SDCard.SDCard import SDCard
from libs.controllers.storage import IStorageController

from uos import mount, umount, VfsFat, mkdir

class SDCardStorageController(IStorageController):

    mounted = False

    def __init__(self, spi: SPI, cs=Pin(1, Pin.OUT)) -> None:
        self.spi = spi
        self.cs = cs

        self.sd = SDCard(self.spi, self.cs)

    def mount(self, mount_point):
        # FIXME: check if already mounted
        self.mounted = True
        self.mount_point = mount_point

        try: 
            vfs = VfsFat(self.sd)
            mount(vfs, mount_point)
        except OSError as e:
            if e.args[0] == 1:
                print('mount failed')


    def umount(self):
        # FIXME: check if already unmounted
        umount(self.mount_point)
        self.mounted = False

    def get_root_path(self):
        return self.mount_point + '/'
