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
            parts = path.split('/')

            for i in range(1, len(parts)):
                try:
                    mkdir('/'.join(parts[:i]))
                except OSError:
                    pass
            # then create the file
            f = open(path, 'w')
            f.close()
