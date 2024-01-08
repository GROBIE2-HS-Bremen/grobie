
from libs.controllers.storage import IStorageController


class LocalStorageController(IStorageController): 

    def __init__(self) -> None:
        pass

    def mount(self, mount_point):
        pass

    def umount(self):
        pass

    def get_root_path(self):
        return '/data/'