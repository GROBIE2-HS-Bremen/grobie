
from uos import mkdir


class IStorageController: 
    def mount(self, mount_point):
        raise NotImplementedError()
    
    def umount(self):
        raise NotImplementedError()

    def get_root_path(self):
        raise NotImplementedError()
    
    def ensure_exists(self, path):
        try:
            f = open(path, 'r')
            f.close()
        except OSError:
            # if not, recursively create the directory
            parts = path.split('/')
            for i in range(1, len(parts)):
                mkdir('/'.join(parts[:i]))

            # then create the file
            f = open(path, 'w')
            f.close()