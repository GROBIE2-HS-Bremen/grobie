
class ITimekeepingController:
    def get_time(self):
        raise NotImplementedError()

    def sync_time(self, unix_timestamp: int):
        raise NotImplementedError()